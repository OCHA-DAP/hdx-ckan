"""
AWS credential helpers: core AssumeRole logic + shared Redis-backed cache.

Layout
------
* ``assume_role_with_instance_profile`` – pure function, no caching, no config.
  All boto3/botocore calls live here.  Tested in isolation in test_aws_credentials.py.

* ``get_cached_aws_credentials`` – validates arguments, then delegates to the
  dogpile-cached ``_get_cached_aws_credentials_impl``.  Validation happens
  before dogpile so that invalid arguments never trigger a Redis round-trip.
  ``get_cached_aws_credentials.invalidate`` is proxied from the cached impl so
  callers can invalidate entries without knowing about the internal split.

  Because ``cache_on_arguments()`` includes every parameter in the Redis key,
  different (role_arn, region, session_name) tuples produce independent cache
  entries.  S3 and SES therefore share one dogpile region but never collide.

* ``get_credentials_info`` – generic monitoring helper.  Accepts any
  zero-argument callable that returns a credentials dict (e.g.
  ``get_cached_s3_credentials`` or ``get_cached_ses_credentials``).
  Always returns a dict – never raises.

Usage in a plugin
-----------------
    from ckanext.hdx_theme.helpers.aws_credentials import (
        AwsAssumeRoleException,
        get_cached_aws_credentials,
        get_credentials_info,
    )

    def get_cached_my_service_credentials():
        role_arn = config.get('ckanext.myplugin.role_arn')
        region   = config.get('ckanext.myplugin.region')
        session  = config.get('ckanext.myplugin.session_name', 'ckan-my-session')
        return get_cached_aws_credentials(role_arn, region, session)

    def my_credentials_info():
        return get_credentials_info(get_cached_my_service_credentials)
"""

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict

import boto3
from botocore.credentials import InstanceMetadataFetcher, InstanceMetadataProvider
from botocore.exceptions import BotoCoreError, ClientError

from dogpile.cache import make_region
from ckanext.hdx_theme.helpers.caching import (
    dogpile_config_filter,
    dogpile_standard_config,
    HDXRedisInvalidationStrategy,
)

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dogpile region – shared by all services; keys are differentiated by args.
# Prefixed with _ because it is an implementation detail; callers should use
# get_cached_aws_credentials / get_cached_aws_credentials.invalidate().
#
# TTL is set to 55 min (5 min before the 60 min STS credential lifetime).
# Both redis and local-dbm backends get the same TTL so behaviour is
# consistent between production (Redis) and dev (local file) environments.
# ---------------------------------------------------------------------------

_dogpile_aws_config = {
    **dogpile_standard_config,
    'cache.redis.expiration_time': 60 * 55,   # 55 min – consistent in prod
    'cache.local.expiration_time': 60 * 55,   # 55 min – consistent in dev
}

_dogpile_aws_region = make_region(key_mangler=lambda key: 'aws-creds-' + key)
_dogpile_aws_region.configure_from_config(_dogpile_aws_config, dogpile_config_filter)

if dogpile_config_filter == 'cache.redis.':
    _dogpile_aws_region.region_invalidator = HDXRedisInvalidationStrategy(_dogpile_aws_region)


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class AwsAssumeRoleException(Exception):
    """Raised when an AssumeRole operation fails for any reason."""
    pass


# ---------------------------------------------------------------------------
# Core logic (uncached, pure)
# ---------------------------------------------------------------------------

def assume_role_with_instance_profile(
    role_name_or_arn: str,
    region: str,
    session_name: str,
    duration_seconds: int = 3600,
) -> Dict[str, Any]:
    """
    Assume an IAM role using EC2 instance profile credentials.

    Fetches credentials directly from the EC2 instance metadata endpoint,
    bypassing any AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY environment
    variables so that static dev credentials for other services do not
    interfere with the STS call.

    This function is **not cached**.  Use ``get_cached_aws_credentials``
    for the cached version.

    :param role_name_or_arn: Full IAM role ARN or bare role name.
    :param region: AWS region for the STS client (e.g. ``'us-east-1'``).
    :param session_name: RoleSessionName passed to STS AssumeRole.
    :param duration_seconds: Credential lifetime in seconds (default 3600).
    :return: Dict with keys ``access_key``, ``secret_key``, ``session_token``,
        ``expiration`` (timezone-aware datetime), ``region``.
    :raises AwsAssumeRoleException: For any failure during the AssumeRole flow.
    """
    try:
        log.info('Assuming role %s (session=%s, region=%s)',
                 role_name_or_arn, session_name, region)

        fetcher = InstanceMetadataFetcher(timeout=1, num_attempts=2)
        provider = InstanceMetadataProvider(iam_role_fetcher=fetcher)

        instance_creds = provider.load()
        if instance_creds is None:
            raise AwsAssumeRoleException(
                'Failed to load credentials from EC2 instance metadata'
            )

        base_session = boto3.Session(
            aws_access_key_id=instance_creds.access_key,
            aws_secret_access_key=instance_creds.secret_key,
            aws_session_token=instance_creds.token,
            region_name=region,
        )
        sts_client = base_session.client('sts')

        if role_name_or_arn.startswith('arn:aws:iam::'):
            full_role_arn = role_name_or_arn
        else:
            account_id = sts_client.get_caller_identity()['Account']
            full_role_arn = 'arn:aws:iam::{}:role/{}'.format(account_id, role_name_or_arn)

        log.info('Calling STS AssumeRole: arn=%s', full_role_arn)

        assumed = sts_client.assume_role(
            RoleArn=full_role_arn,
            RoleSessionName=session_name,
            DurationSeconds=duration_seconds,
        )

        expiration = assumed['Credentials']['Expiration']
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        credentials = {
            'access_key': assumed['Credentials']['AccessKeyId'],
            'secret_key': assumed['Credentials']['SecretAccessKey'],
            'session_token': assumed['Credentials']['SessionToken'],
            'expiration': expiration,
            'region': region,
        }

        minutes_left = int(
            (expiration - datetime.now(timezone.utc)).total_seconds() / 60
        )
        log.info('AssumeRole succeeded for %s, credentials expire at %s (in %d min)',
                 full_role_arn,
                 expiration.strftime('%Y-%m-%d %H:%M:%S UTC'),
                 minutes_left)

        return credentials

    except AwsAssumeRoleException:
        raise
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', 'Unknown')
        msg = e.response.get('Error', {}).get('Message', str(e))
        log.error('AWS ClientError during AssumeRole: %s - %s', code, msg)
        raise AwsAssumeRoleException('AWS API error: {} - {}'.format(code, msg))
    except BotoCoreError as e:
        log.error('BotoCoreError during AssumeRole: %s', e)
        raise AwsAssumeRoleException('Boto error: {}'.format(e))
    except Exception as e:
        log.error('Unexpected error during AssumeRole: %s', e, exc_info=True)
        raise AwsAssumeRoleException('Unexpected error: {}'.format(e))


# ---------------------------------------------------------------------------
# Cached wrapper (shared by all callers)
#
# Split into two layers so that argument validation fires *before* dogpile
# generates a cache key and hits Redis.  Invalid arguments are rejected
# immediately without any backend I/O.
# ---------------------------------------------------------------------------

@_dogpile_aws_region.cache_on_arguments()
def _get_cached_aws_credentials_impl(
    role_name_or_arn: str,
    region: str,
    session_name: str,
) -> Dict[str, Any]:
    """Internal dogpile-cached implementation – do not call directly."""
    return assume_role_with_instance_profile(role_name_or_arn, region, session_name)


def get_cached_aws_credentials(
    role_name_or_arn: str,
    region: str,
    session_name: str,
) -> Dict[str, Any]:
    """
    Return temporary AWS credentials via AssumeRole, cached in Redis via dogpile.

    Validates arguments before delegating to the dogpile-cached implementation,
    so invalid arguments never cause a Redis round-trip.

    ``cache_on_arguments()`` incorporates all three parameters into the Redis
    key, so callers with different (role_arn, region, session_name) tuples
    get independent cache entries even though they share this single function
    and dogpile region.

    Credentials are valid for 60 minutes; the dogpile TTL is 55 minutes so
    the cache is always refreshed at least 5 minutes before expiry.

    :param role_name_or_arn: Full IAM role ARN or bare role name.
    :param region: AWS region (e.g. ``'us-east-1'``).
    :param session_name: RoleSessionName – also acts as the per-caller cache
        discriminator (e.g. ``'ckan-s3filestore-session'`` vs
        ``'ckan-ses-session'``).
    :return: Dict with keys ``access_key``, ``secret_key``, ``session_token``,
        ``expiration``, ``region``.
    :raises AwsAssumeRoleException: If arguments are missing or credential
        loading fails.
    """
    if not role_name_or_arn:
        raise AwsAssumeRoleException('role_name_or_arn is required')
    if not region:
        raise AwsAssumeRoleException('region is required')
    if not session_name or not session_name.strip():
        raise AwsAssumeRoleException('session_name is required')

    session_name = session_name.strip()
    return _get_cached_aws_credentials_impl(role_name_or_arn, region, session_name)


# Proxy invalidate so callers can use get_cached_aws_credentials.invalidate(...)
# without needing to know about the internal impl function.
get_cached_aws_credentials.invalidate = _get_cached_aws_credentials_impl.invalidate


# ---------------------------------------------------------------------------
# Generic monitoring helper
# ---------------------------------------------------------------------------

def get_credentials_info(credentials_fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    """
    Return a monitoring dict for any zero-argument credential-loading function.

    Always returns a dict – never raises – so monitoring endpoints and startup
    code can call this safely regardless of backend availability.

    :param credentials_fn: Callable with no arguments that returns a credentials
        dict (e.g. ``get_cached_s3_credentials`` or ``get_cached_ses_credentials``).
    :return: Dict with ``has_credentials`` (bool) and either credential details
        or an ``error`` string.
    """
    try:
        credentials = credentials_fn()

        now = datetime.now(timezone.utc)
        expiration = credentials['expiration']
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        access_key = credentials.get('access_key', 'N/A')
        masked_key = (
            '{}***{}'.format(access_key[:4], access_key[-4:])
            if len(access_key) > 8
            else access_key
        )

        return {
            'has_credentials': True,
            'expiration_time': str(expiration),
            'time_until_expiry': str(expiration - now),
            'region': credentials.get('region'),
            'access_key': masked_key,
        }
    except Exception as e:
        return {
            'has_credentials': False,
            'error': str(e),
        }
