import logging
import boto3
import botocore

import ckan.lib.munge as munge
import ckan.plugins.toolkit as tk
from ckanext.hdx_theme.helpers.exception import BaseHdxException

from ckanext.s3filestore.uploader import S3ResourceUploader

_config = tk.config
_get_action = tk.get_action

log = logging.getLogger(__name__)


def tag_s3_version_by_resource_id(context, resource_id, in_quarantine):
    '''
    :param context:
    :type context: dict
    :param resource_id:
    :type resource_id: str
    :param in_quarantine:
    :type in_quarantine: bool
    '''
    resource_dict = _get_action('resource_show')(context, {'id': resource_id})
    return tag_s3_version(resource_dict['id'], resource_dict['url'], in_quarantine)


def tag_s3_version(resource_id, resource_url, in_quarantine):
    '''
        :param resource_id:
        :type resource_id: str
        :param resource_url:
        :type resource_url: str
        :param in_quarantine:
        :type in_quarantine: bool
        '''
    try:
        uploader = S3ResourceUploader({})
        client = _create_s3_client()
        munged_resource_name = munge.munge_filename(resource_url)
        filepath = uploader.get_path(resource_id, munged_resource_name)
        bucket_name = _config.get('ckanext.s3filestore.aws_bucket_name')
        client.put_object_tagging(
            Bucket=bucket_name,
            Key=filepath,
            Tagging={
                'TagSet': _create_tag_set(in_quarantine)
            },
        )
    except Exception as e:
        msg = 'Couldn\'t tag S3 object {}'.format(str(e))
        log.warning(msg)
        raise S3VersionTaggingException(msg)


def _create_s3_client():
    p_key = _config.get('ckanext.s3filestore.aws_access_key_id')
    s_key = _config.get('ckanext.s3filestore.aws_secret_access_key')
    region = _config.get('ckanext.s3filestore.region_name')
    signature = _config.get('ckanext.s3filestore.signature_version')
    host_name = _config.get('ckanext.s3filestore.host_name')

    session = boto3.session.Session(aws_access_key_id=p_key,
                                    aws_secret_access_key=s_key,
                                    region_name=region)
    s3 = session.resource('s3', endpoint_url=host_name,
                          config=botocore.client.Config(signature_version=signature))

    return s3.meta.client


def _create_tag_set(in_quarantine):
    return [
        {
            'Key': 'Sensitive',
            'Value': 'yes'
        },
    ] if in_quarantine else []


class S3VersionTaggingException(BaseHdxException):
    pass
