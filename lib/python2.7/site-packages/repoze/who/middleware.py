import logging
from StringIO import StringIO
import sys

from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IAuthenticator
from repoze.who.interfaces import IChallenger
from repoze.who.interfaces import IMetadataProvider

_STARTED = '-- repoze.who request started (%s) --'
_ENDED = '-- repoze.who request ended (%s) --'

class PluggableAuthenticationMiddleware(object):
    def __init__(self, app,
                 identifiers,
                 authenticators,
                 challengers,
                 mdproviders,
                 classifier,
                 challenge_decider,
                 log_stream = None,
                 log_level = logging.INFO,
                 remote_user_key = 'REMOTE_USER',
                 ):
        iregistry, nregistry = make_registries(identifiers, authenticators,
                                               challengers, mdproviders)
        self.registry = iregistry
        self.name_registry = nregistry
        self.app = app
        self.classifier = classifier
        self.challenge_decider = challenge_decider
        self.remote_user_key = remote_user_key
        self.logger = None
        if isinstance(log_stream, logging.Logger):
            self.logger = log_stream
        elif log_stream:
            handler = logging.StreamHandler(log_stream)
            fmt = '%(asctime)s %(message)s'
            formatter = logging.Formatter(fmt)
            handler.setFormatter(formatter)
            self.logger = logging.Logger('repoze.who')
            self.logger.addHandler(handler)
            self.logger.setLevel(log_level)

    def __call__(self, environ, start_response):
        if self.remote_user_key in environ:
            # act as a pass through if REMOTE_USER (or whatever) is
            # already set
            return self.app(environ, start_response)

        path_info = environ.get('PATH_INFO', None)

        environ['repoze.who.plugins'] = self.name_registry
        environ['repoze.who.logger'] = self.logger
        environ['repoze.who.application'] = self.app

        logger = self.logger
        logger and logger.info(_STARTED % path_info)
        classification = self.classifier(environ)
        logger and logger.info('request classification: %s' % classification)
        userid = None
        identity = None
        identifier = None

        ids = self.identify(environ, classification)
            
        # ids will be list of tuples: [ (IIdentifier, identity) ]
        if ids:
            auth_ids = self.authenticate(environ, classification, ids)

            # auth_ids will be a list of five-tuples in the form
            #  ( (auth_rank, id_rank), authenticator, identifier, identity,
            #    userid )
            #
            # When sorted, its first element will represent the "best"
            # identity for this request.

            if auth_ids:
                auth_ids.sort()
                best = auth_ids[0]
                rank, authenticator, identifier, identity, userid = best
                identity = Identity(identity) # dont show contents at print

                # allow IMetadataProvider plugins to scribble on the identity
                self.add_metadata(environ, classification, identity)

                # add the identity to the environment; a downstream
                # application can mutate it to do an 'identity reset'
                # as necessary, e.g. identity['login'] = 'foo',
                # identity['password'] = 'bar'
                environ['repoze.who.identity'] = identity
                # set the REMOTE_USER
                environ[self.remote_user_key] = userid

        else:
            logger and logger.info('no identities found, not authenticating')

        # allow identifier plugins to replace the downstream
        # application (to do redirection and unauthorized themselves
        # mostly)
        app = environ.pop('repoze.who.application')
        if  app is not self.app:
            logger and logger.info(
                'static downstream application replaced with %s' % app)

        wrapper = StartResponseWrapper(start_response)
        app_iter = app(environ, wrapper.wrap_start_response)

        # The challenge decider almost(?) always needs information from the
        # response.  The WSGI spec (PEP 333) states that a WSGI application
        # must call start_response by the iterable's first iteration.  If
        # start_response hasn't been called, we'll wrap it in a way that
        # triggers that call.
        if not wrapper.called:
            app_iter = wrap_generator(app_iter)

        if self.challenge_decider(environ, wrapper.status, wrapper.headers):
            logger and logger.info('challenge required')

            challenge_app = self.challenge(
                environ,
                classification,
                wrapper.status,
                wrapper.headers,
                identifier,
                identity
                )
            if challenge_app is not None:
                logger and logger.info('executing challenge app')
                if app_iter:
                    list(app_iter) # unwind the original app iterator
                # replace the downstream app with the challenge app
                app_iter = challenge_app(environ, start_response)
            else:
                logger and logger.info('configuration error: no challengers')
                raise RuntimeError('no challengers found')
        else:
            logger and logger.info('no challenge required')
            remember_headers = []
            if identifier:
                remember_headers = identifier.remember(environ, identity)
                if remember_headers:
                    logger and logger.info('remembering via headers from %s: %s'
                                           % (identifier, remember_headers))
            wrapper.finish_response(remember_headers)

        logger and logger.info(_ENDED % path_info)
        return app_iter

    def identify(self, environ, classification):
        logger = self.logger
        candidates = self.registry.get(IIdentifier, ())
        logger and self.logger.info('identifier plugins registered %s' %
                                    (candidates,))
        plugins = match_classification(IIdentifier, candidates, classification)
        logger and self.logger.info(
            'identifier plugins matched for '
            'classification "%s": %s' % (classification, plugins))

        results = []
        for plugin in plugins:
            identity = plugin.identify(environ)
            if identity is not None:
                logger and logger.debug(
                    'identity returned from %s: %s' % (plugin, identity))
                results.append((plugin, identity))
            else:
                logger and logger.debug(
                    'no identity returned from %s (%s)' % (plugin, identity))

        logger and logger.debug('identities found: %s' % (results,))
        return results

    def add_metadata(self, environ, classification, identity):
        candidates = self.registry.get(IMetadataProvider, ())
        plugins = match_classification(IMetadataProvider, candidates,
                                       classification)        
        for plugin in plugins:
            plugin.add_metadata(environ, identity)

    def authenticate(self, environ, classification, identities):
        logger = self.logger
        candidates = self.registry.get(IAuthenticator, [])
        logger and self.logger.info('authenticator plugins registered %s' %
                                    candidates)
        plugins = match_classification(IAuthenticator, candidates,
                                       classification)
        logger and self.logger.info(
            'authenticator plugins matched for '
            'classification "%s": %s' % (classification, plugins))

        # 'preauthenticated' identities are considered best-ranking
        identities, results, id_rank_start =self._filter_preauthenticated(
            identities)

        auth_rank = 0

        for plugin in plugins:
            identifier_rank = id_rank_start
            for identifier, identity in identities:
                userid = plugin.authenticate(environ, identity)
                if userid is not None:
                    logger and logger.debug(
                        'userid returned from %s: "%s"' % (plugin, userid))

                    # stamp the identity with the userid
                    identity['repoze.who.userid'] = userid
                    rank = (auth_rank, identifier_rank)
                    results.append(
                        (rank, plugin, identifier, identity, userid)
                        )
                else:
                    logger and logger.debug(
                        'no userid returned from %s: (%s)' % (
                        plugin, userid))
                identifier_rank += 1
            auth_rank += 1

        logger and logger.debug('identities authenticated: %s' % (results,))
        return results

    def _filter_preauthenticated(self, identities):
        logger = self.logger
        results = []
        new_identities = identities[:]

        identifier_rank = 0
        for thing in identities:
            identifier, identity = thing
            userid = identity.get('repoze.who.userid')
            if userid is not None:
                # the identifier plugin has already authenticated this
                # user (domain auth, auth ticket, etc)
                logger and logger.info(
                  'userid preauthenticated by %s: "%s" '
                  '(repoze.who.userid set)' % (identifier, userid)
                  )
                rank = (0, identifier_rank)
                results.append(
                    (rank, None, identifier, identity, userid)
                    )
                identifier_rank += 1
                new_identities.remove(thing)
        return new_identities, results, identifier_rank

    def challenge(self, environ, classification, status, app_headers,
                  identifier, identity):
        # happens on egress
        logger = self.logger

        forget_headers = []

        if identifier:
            forget_headers = identifier.forget(environ, identity)
            if forget_headers is None:
                forget_headers = []
            else:
                logger and logger.info('forgetting via headers from %s: %s'
                                       % (identifier, forget_headers))

        candidates = self.registry.get(IChallenger, ())
        logger and logger.info('challengers registered: %s' % candidates)
        plugins = match_classification(IChallenger,
                                       candidates, classification)
        logger and logger.info('challengers matched for '
                               'classification "%s": %s' % (classification,
                                                            plugins))
        for plugin in plugins:
            app = plugin.challenge(environ, status, app_headers,
                                   forget_headers)
            if app is not None:
                # new WSGI application
                logger and logger.info(
                    'challenger plugin %s "challenge" returned an app' % (
                    plugin))
                return app

        # signifies no challenge
        logger and logger.info('no challenge app returned')
        return None

def wrap_generator(result):
    """\
    This function returns a generator that behaves exactly the same as the
    original.  It's only difference is it pulls the first iteration off and
    caches it to trigger any immediate side effects (in a WSGI world, this
    ensures start_response is called).
    """
    # Neat trick to pull the first iteration only. We need to do this outside
    # of the generator function to ensure it is called.
    for iter in result:
        first = iter
        break

    # Wrapper yields the first iteration, then passes result's iterations
    # directly up.
    def wrapper():
        yield first
        for iter in result:
            # We'll let result's StopIteration bubble up directly.
            yield iter
    return wrapper()

def match_classification(iface, plugins, classification):
    result = []
    for plugin in plugins:
        
        plugin_classifications = getattr(plugin, 'classifications', {})
        iface_classifications = plugin_classifications.get(iface)
        if not iface_classifications: # good for any
            result.append(plugin)
            continue
        if classification in iface_classifications:
            result.append(plugin)

    return result

class StartResponseWrapper(object):
    def __init__(self, start_response):
        self.start_response = start_response
        self.status = None
        self.headers = []
        self.exc_info = None
        self.buffer = StringIO()
        # A WSGI app may delay calling start_response until the first iteration
        # of its generator.  We track this so we know whether or not we need to
        # trigger an iteration before examining the response.
        self.called = False

    def wrap_start_response(self, status, headers, exc_info=None):
        self.headers = headers
        self.status = status
        self.exc_info = exc_info
        # The response has been initiated, so we have a valid code.
        self.called = True
        return self.buffer.write

    def finish_response(self, extra_headers):
        if not extra_headers:
            extra_headers = []
        headers = self.headers + extra_headers
        write = self.start_response(self.status, headers, self.exc_info)
        if write:
            self.buffer.seek(0)
            value = self.buffer.getvalue()
            if value:
                write(value)
            if hasattr(write, 'close'):
                write.close()

def make_test_middleware(app, global_conf):
    """ Functionally equivalent to

    [plugin:form]
    use = repoze.who.plugins.form.FormPlugin
    rememberer_name = cookie
    login_form_qs=__do_login

    [plugin:cookie]
    use = repoze.who.plugins.cookie:InsecureCookiePlugin
    cookie_name = oatmeal

    [plugin:basicauth]
    use = repoze.who.plugins.basicauth.BasicAuthPlugin
    realm = repoze.who

    [plugin:htpasswd]
    use = repoze.who.plugins.htpasswd.HTPasswdPlugin
    filename = <...>
    check_fn = repoze.who.plugins.htpasswd:crypt_check

    [general]
    request_classifier = repoze.who.classifiers:default_request_classifier
    challenge_decider = repoze.who.classifiers:default_challenge_decider

    [identifiers]
    plugins = form:browser cookie basicauth

    [authenticators]
    plugins = htpasswd

    [challengers]
    plugins = form:browser basicauth
    """
    # be able to test without a config file
    from repoze.who.plugins.basicauth import BasicAuthPlugin
    from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
    from repoze.who.plugins.cookie import InsecureCookiePlugin
    from repoze.who.plugins.form import FormPlugin
    from repoze.who.plugins.htpasswd import HTPasswdPlugin
    io = StringIO()
    salt = 'aa'
    for name, password in [ ('admin', 'admin'), ('chris', 'chris') ]:
        io.write('%s:%s\n' % (name, password))
    io.seek(0)
    def cleartext_check(password, hashed):
        return password == hashed #pragma NO COVERAGE
    htpasswd = HTPasswdPlugin(io, cleartext_check)
    basicauth = BasicAuthPlugin('repoze.who')
    auth_tkt = AuthTktCookiePlugin('secret', 'auth_tkt')
    cookie = InsecureCookiePlugin('oatmeal')
    form = FormPlugin('__do_login', rememberer_name='auth_tkt')
    form.classifications = { IIdentifier:['browser'],
                             IChallenger:['browser'] } # only for browser
    identifiers = [('form', form),('auth_tkt',auth_tkt),('basicauth',basicauth)]
    authenticators = [('htpasswd', htpasswd)]
    challengers = [('form',form), ('basicauth',basicauth)]
    mdproviders = []
    from repoze.who.classifiers import default_request_classifier
    from repoze.who.classifiers import default_challenge_decider
    log_stream = None
    import os
    if os.environ.get('WHO_LOG'):
        log_stream = sys.stdout
    middleware = PluggableAuthenticationMiddleware(
        app,
        identifiers,
        authenticators,
        challengers,
        mdproviders,
        default_request_classifier,
        default_challenge_decider,
        log_stream = log_stream,
        log_level = logging.DEBUG
        )
    return middleware

def verify(plugin, iface):
    from zope.interface.verify import verifyObject
    verifyObject(iface, plugin, tentative=True)
    
def make_registries(identifiers, authenticators, challengers, mdproviders):
    from zope.interface.verify import BrokenImplementation
    interface_registry = {}
    name_registry = {}

    for supplied, iface in [ (identifiers, IIdentifier),
                             (authenticators, IAuthenticator),
                             (challengers, IChallenger),
                             (mdproviders, IMetadataProvider)]:

        for name, value in supplied:
            try:
                verify(value, iface)
            except BrokenImplementation, why:
                why = str(why)
                raise ValueError(str(name) + ': ' + why)
            L = interface_registry.setdefault(iface, [])
            L.append(value)
            name_registry[name] = value

    return interface_registry, name_registry

class Identity(dict):
    """ dict subclass that prevents its members from being rendered
    during print """
    def __repr__(self):
        return '<repoze.who identity (hidden, dict-like) at %s>' % id(self)
    __str__ = __repr__


