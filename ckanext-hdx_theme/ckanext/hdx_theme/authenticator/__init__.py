from zope.interface import implementer
from repoze.who.interfaces import IAuthenticator


# Based on PR from ckanext-security to CKAN: https://github.com/ckan/ckan/pull/4656/files
@implementer(IAuthenticator)
class BeakerRedisAuth(object):

    def authenticate(self, environ, identity):
        # At this stage, the identity has already been validated from the cookie
        # and redis (use_beaker middleware). We simply return the user id
        # from the identity object if it's there, or None if the user's
        # identity is not verified.
        return identity.get('repoze.who.userid', None)
