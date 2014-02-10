import binascii

from paste.httpheaders import WWW_AUTHENTICATE
from paste.httpheaders import AUTHORIZATION
from paste.httpexceptions import HTTPUnauthorized

from zope.interface import implements

from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IChallenger

class BasicAuthPlugin(object):

    implements(IIdentifier, IChallenger)
    
    def __init__(self, realm):
        self.realm = realm

    # IIdentifier
    def identify(self, environ):
        authorization = AUTHORIZATION(environ)
        try:
            authmeth, auth = authorization.split(' ', 1)
        except ValueError: # not enough values to unpack
            return None
        if authmeth.lower() == 'basic':
            try:
                auth = auth.strip().decode('base64')
            except binascii.Error: # can't decode
                return None
            try:
                login, password = auth.split(':', 1)
            except ValueError: # not enough values to unpack
                return None
            auth = {'login':login, 'password':password}
            return auth

        return None

    # IIdentifier
    def remember(self, environ, identity):
        # we need to do nothing here; the browser remembers the basic
        # auth info as a result of the user typing it in.
        pass

    def _get_wwwauth(self):
        head = WWW_AUTHENTICATE.tuples('Basic realm="%s"' % self.realm)
        return head

    # IIdentifier
    def forget(self, environ, identity):
        return self._get_wwwauth()

    # IChallenger
    def challenge(self, environ, status, app_headers, forget_headers):
        head = self._get_wwwauth()
        if head[0] not in forget_headers:
            head = head + forget_headers
        return HTTPUnauthorized(headers=head)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            id(self)) #pragma NO COVERAGE

def make_plugin(realm='basic'):
    plugin = BasicAuthPlugin(realm)
    return plugin

