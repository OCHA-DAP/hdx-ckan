import zope.interface 
from repoze.who.interfaces import IChallengeDecider


def openid_challenge_decider(environ, status, headers):
    # we do the default if it's a 401, probably we show a form then
    if status.startswith('401 '):
        return True
    elif environ.has_key('repoze.whoplugins.openid.openid'):
        # in case IIdentification found an openid it should be in the environ
        # and we do the challenge
        return True
    return False
    
zope.interface.directlyProvides(openid_challenge_decider, IChallengeDecider)

