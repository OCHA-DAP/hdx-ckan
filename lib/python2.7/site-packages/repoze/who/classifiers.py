from paste.httpheaders import REQUEST_METHOD
from paste.httpheaders import CONTENT_TYPE
from paste.httpheaders import USER_AGENT
from paste.httpheaders import WWW_AUTHENTICATE

import zope.interface
from repoze.who.interfaces import IRequestClassifier
from repoze.who.interfaces import IChallengeDecider

_DAV_METHODS = (
    'OPTIONS',
    'PROPFIND',
    'PROPPATCH',
    'MKCOL',
    'LOCK',
    'UNLOCK',
    'TRACE',
    'DELETE',
    'COPY',
    'MOVE'
    )

_DAV_USERAGENTS = (
    'Microsoft Data Access Internet Publishing Provider',
    'WebDrive',
    'Zope External Editor',
    'WebDAVFS',
    'Goliath',
    'neon',
    'davlib',
    'wsAPI',
    'Microsoft-WebDAV'
    )

def default_request_classifier(environ):
    """ Returns one of the classifiers 'dav', 'xmlpost', or 'browser',
    depending on the imperative logic below"""
    request_method = REQUEST_METHOD(environ)
    if request_method in _DAV_METHODS:
        return 'dav'
    useragent = USER_AGENT(environ)
    if useragent:
        for agent in _DAV_USERAGENTS:
            if useragent.find(agent) != -1:
                return 'dav'
    if request_method == 'POST':
        if CONTENT_TYPE(environ) == 'text/xml':
            return 'xmlpost'
    return 'browser'
zope.interface.directlyProvides(default_request_classifier, IRequestClassifier)

def default_challenge_decider(environ, status, headers):
    return status.startswith('401 ')
zope.interface.directlyProvides(default_challenge_decider, IChallengeDecider)

def passthrough_challenge_decider(environ, status, headers):
    """ Don't challenge for pre-challenged responses.

    o Assume responsese with 'WWW-Authenticate' or an HTML content type
      are pre-challenged.
    """
    if not status.startswith('401 '):
        return False
    h_dict = dict(headers)
    if 'WWW-Authenticate' in h_dict:
        return False
    ct = h_dict.get('Content-Type')
    if ct is not None:
        return not ct.startswith('text/html')
    return True
zope.interface.directlyProvides(passthrough_challenge_decider,
                                IChallengeDecider)
