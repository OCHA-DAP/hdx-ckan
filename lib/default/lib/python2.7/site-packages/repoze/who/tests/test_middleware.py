import unittest

class TestMiddleware(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.middleware import PluggableAuthenticationMiddleware
        return PluggableAuthenticationMiddleware

    def _makeOne(self,
                 app=None,
                 identifiers=None,
                 authenticators=None,
                 challengers=None,
                 classifier=None,
                 mdproviders=None,
                 challenge_decider=None,
                 log_stream=None,
                 log_level=None,
                 ):
        if app is None:
            app = DummyApp()
        if identifiers is None:
            identifiers = []
        if authenticators is None:
            authenticators = []
        if challengers is None:
            challengers = []
        if classifier is None:
            classifier = DummyRequestClassifier()
        if mdproviders is None:
            mdproviders = []
        if challenge_decider is None:
            challenge_decider = DummyChallengeDecider()
        if log_level is None:
            import logging
            log_level = logging.DEBUG
        mw = self._getTargetClass()(app,
                                    identifiers,
                                    authenticators,
                                    challengers,
                                    mdproviders,
                                    classifier,
                                    challenge_decider,
                                    log_stream,
                                    log_level=logging.DEBUG)
        return mw

    def _makeEnviron(self, kw=None):
        environ = {}
        environ['wsgi.version'] = (1,0)
        if kw is not None:
            environ.update(kw)
        return environ

    def test_accepts_logger(self):
        import logging
        logger = logging.Logger('something')
        logger.setLevel(logging.INFO)
        mw = self._makeOne(log_stream=logger)
        self.assertEqual(logger, mw.logger)

    def test_identify_success(self):
        environ = self._makeEnviron()
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('i', identifier) ]
        mw = self._makeOne(identifiers=identifiers)
        results = mw.identify(environ, None)
        self.assertEqual(len(results), 1)
        new_identifier, identity = results[0]
        self.assertEqual(new_identifier, identifier)
        self.assertEqual(identity['login'], 'chris')
        self.assertEqual(identity['password'], 'password')

    def test_identify_success_empty_identity(self):
        environ = self._makeEnviron()
        identifier = DummyIdentifier({})
        identifiers = [ ('i', identifier) ]
        mw = self._makeOne(identifiers=identifiers)
        results = mw.identify(environ, None)
        self.assertEqual(len(results), 1)
        new_identifier, identity = results[0]
        self.assertEqual(new_identifier, identifier)
        self.assertEqual(identity, {})

    def test_identify_fail(self):
        environ = self._makeEnviron()
        plugin = DummyNoResultsIdentifier()
        plugins = [ ('dummy', plugin) ]
        mw = self._makeOne(identifiers=plugins)
        results = mw.identify(environ, None)
        self.assertEqual(len(results), 0)

    def test_identify_success_skip_noresults(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyNoResultsIdentifier()
        credentials = {'login':'chris', 'password':'password'}
        plugin2 = DummyIdentifier(credentials)
        plugins = [ ('identifier1', plugin1), ('identifier2', plugin2) ]
        mw = self._makeOne(identifiers=plugins)
        results = mw.identify(environ, None)
        self.assertEqual(len(results), 1)
        new_identifier, identity = results[0]
        self.assertEqual(new_identifier, plugin2)
        self.assertEqual(identity['login'], 'chris')
        self.assertEqual(identity['password'], 'password')

    def test_identify_success_multiresults(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyIdentifier({'login':'fred','password':'fred'})
        plugin2 = DummyIdentifier({'login':'bob','password':'bob'})
        plugins = [ ('identifier1', plugin1), ('identifier2', plugin2) ]
        mw = self._makeOne(identifiers=plugins)
        results = mw.identify(environ, None)
        self.assertEqual(len(results), 2)
        new_identifier, identity = results[0]
        self.assertEqual(new_identifier, plugin1)
        self.assertEqual(identity['login'], 'fred')
        self.assertEqual(identity['password'], 'fred')
        new_identifier, identity = results[1]
        self.assertEqual(new_identifier, plugin2)
        self.assertEqual(identity['login'], 'bob')
        self.assertEqual(identity['password'], 'bob')

    def test_identify_find_implicit_classifier(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyIdentifier({'login':'fred','password':'fred'})
        from repoze.who.interfaces import IIdentifier
        plugin1.classifications = {IIdentifier:['nomatch']}
        plugin2 = DummyIdentifier({'login':'bob','password':'bob'})
        plugins = [ ('identifier1', plugin1),  ('identifier2', plugin2) ]
        mw = self._makeOne(identifiers=plugins)
        results = mw.identify(environ, 'match')
        self.assertEqual(len(results), 1)
        plugin, creds = results[0]
        self.assertEqual(creds['login'], 'bob')
        self.assertEqual(creds['password'], 'bob')
        self.assertEqual(plugin, plugin2)

    def test_identify_find_explicit_classifier(self):
        environ = self._makeEnviron()
        from repoze.who.interfaces import IIdentifier
        plugin1 = DummyIdentifier({'login':'fred','password':'fred'})
        plugin1.classifications = {IIdentifier:['nomatch']}
        plugin2 = DummyIdentifier({'login':'bob','password':'bob'})
        plugin2.classifications = {IIdentifier:['match']}
        plugins= [ ('identifier1', plugin1), ('identifier2', plugin2) ]
        mw = self._makeOne(identifiers=plugins)
        results = mw.identify(environ, 'match')
        self.assertEqual(len(results), 1)
        plugin, creds = results[0]
        self.assertEqual(creds['login'], 'bob')
        self.assertEqual(creds['password'], 'bob')
        self.assertEqual(plugin, plugin2)

    def test_authenticate_success(self):
        environ = self._makeEnviron()
        plugin1 = DummyAuthenticator('a')
        plugins = [ ('identifier1', plugin1) ]
        mw = self._makeOne(authenticators=plugins)
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, None, identities)
        self.assertEqual(len(results), 1)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,0))
        self.assertEqual(authenticator, plugin1)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'a')

    def test_authenticate_fail(self):
        environ = self._makeEnviron()
        mw = self._makeOne() # no authenticators
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        result = mw.authenticate(environ, None, identities)
        self.assertEqual(len(result), 0)

    def test_authenticate_success_skip_fail(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyFailAuthenticator()
        plugin2 = DummyAuthenticator()
        plugins = [ ('dummy1', plugin1), ('dummy2', plugin2) ]
        mw = self._makeOne(authenticators=plugins)
        creds = {'login':'chris', 'password':'password'}
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, None, identities)
        self.assertEqual(len(results), 1)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (1,0))
        self.assertEqual(authenticator, plugin2)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris')

    def test_authenticate_success_multiresult(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyAuthenticator('chris_id1')
        plugin2 = DummyAuthenticator('chris_id2')
        plugins = [ ('dummy1',plugin1), ('dummy2',plugin2) ]
        mw = self._makeOne(authenticators=plugins)
        creds = {'login':'chris', 'password':'password'}
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, None, identities)
        self.assertEqual(len(results), 2)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,0,))
        self.assertEqual(authenticator, plugin1)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id1')
        result = results[1]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (1,0))
        self.assertEqual(authenticator, plugin2)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id2')

    def test_authenticate_find_implicit_classifier(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        plugin1 = DummyAuthenticator('chris_id1')
        from repoze.who.interfaces import IAuthenticator
        plugin1.classifications = {IAuthenticator:['nomatch']}
        plugin2 = DummyAuthenticator('chris_id2')
        plugins = [ ('auth1', plugin1), ('auth2', plugin2) ]
        mw = self._makeOne(authenticators = plugins)
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, 'match', identities)
        self.assertEqual(len(results), 1)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,0))
        self.assertEqual(authenticator, plugin2)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id2')

    def test_authenticate_find_explicit_classifier(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        from repoze.who.interfaces import IAuthenticator
        plugin1 = DummyAuthenticator('chris_id1')
        plugin1.classifications = {IAuthenticator:['nomatch']}
        plugin2 = DummyAuthenticator('chris_id2')
        plugin2.classifications = {IAuthenticator:['match']}
        plugins = [ ('auth1', plugin1), ('auth2', plugin2) ]
        mw = self._makeOne(authenticators = plugins)
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, 'match', identities)
        self.assertEqual(len(results), 1)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0, 0))
        self.assertEqual(authenticator, plugin2)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id2')

    def test_authenticate_user_null_but_not_none(self):
        environ = self._makeEnviron()
        plugin1 = DummyAuthenticator(0)
        plugins = [ ('identifier1', plugin1) ]
        mw = self._makeOne(authenticators=plugins)
        identities = [ (None, {'login':'chris', 'password':'password'}) ]
        results = mw.authenticate(environ, None, identities)
        self.assertEqual(len(results), 1)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,0))
        self.assertEqual(authenticator, plugin1)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 0)

    def test_authenticate_success_multiresult_one_preauthenticated(self):
        environ = self._makeEnviron()
        mw = self._makeOne()
        preauth = DummyIdentifier({'repoze.who.userid':'preauthenticated'})
        plugin1 = DummyAuthenticator('chris_id1')
        plugin2 = DummyAuthenticator('chris_id2')
        plugins = [ ('dummy1',plugin1), ('dummy2',plugin2) ]
        mw = self._makeOne(authenticators=plugins)
        creds = {'login':'chris', 'password':'password'}
        identities = [ (None, {'login':'chris', 'password':'password'}),
                       (preauth, preauth.credentials) ]
        results = mw.authenticate(environ, None, identities)
        self.assertEqual(len(results), 3)
        result = results[0]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,0,))
        self.assertEqual(authenticator, None)
        self.assertEqual(identifier, preauth)
        self.assertEqual(creds['repoze.who.userid'], 'preauthenticated')
        self.assertEqual(userid, 'preauthenticated')
        result = results[1]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (0,1))
        self.assertEqual(authenticator, plugin1)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id1')
        result = results[2]
        rank, authenticator, identifier, creds, userid = result
        self.assertEqual(rank, (1,1))
        self.assertEqual(authenticator, plugin2)
        self.assertEqual(identifier, None)
        self.assertEqual(creds['login'], 'chris')
        self.assertEqual(creds['password'], 'password')
        self.assertEqual(userid, 'chris_id2')

    def test_challenge_noidentifier_noapp(self):
        environ = self._makeEnviron()
        challenger = DummyChallenger()
        plugins = [ ('challenge', challenger) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        app = mw.challenge(environ, 'match', '401 Unauthorized',
                           [], None, identity)
        self.assertEqual(app, None)
        self.assertEqual(environ['challenged'], app)

    def test_challenge_noidentifier_withapp(self):
        environ = self._makeEnviron()
        app = DummyApp()
        challenger = DummyChallenger(app)
        plugins = [ ('challenge', challenger) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                               [], None, identity)
        self.assertEqual(result, app)
        self.assertEqual(environ['challenged'], app)

    def test_challenge_identifier_noapp(self):
        environ = self._makeEnviron()
        challenger = DummyChallenger()
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        plugins = [ ('challenge', challenger) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                              [], identifier, identity)
        self.assertEqual(result, None)
        self.assertEqual(environ['challenged'], None)
        self.assertEqual(identifier.forgotten, identity)

    def test_challenge_identifier_app(self):
        environ = self._makeEnviron()
        app = DummyApp()
        challenger = DummyChallenger(app)
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        plugins = [ ('challenge', challenger) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                               [], identifier, identity)
        self.assertEqual(result, app)
        self.assertEqual(environ['challenged'], app)
        self.assertEqual(identifier.forgotten, identity)

    def test_challenge_identifier_forget_headers(self):
        FORGET_HEADERS = [('X-testing-forget', 'Oubliez!')]
        environ = self._makeEnviron()
        app = DummyApp()
        challenger = DummyChallenger(app)
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials,
                                     forget_headers=FORGET_HEADERS)
        plugins = [ ('challenge', challenger) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                               [], identifier, identity)

    def test_multi_challenge_firstwins(self):
        environ = self._makeEnviron()
        app1 = DummyApp()
        app2 = DummyApp()
        challenger1 = DummyChallenger(app1)
        challenger2 = DummyChallenger(app2)
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        plugins = [ ('challenge1', challenger1), ('challenge2', challenger2) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                              [], identifier, identity)
        self.assertEqual(result, app1)
        self.assertEqual(environ['challenged'], app1)
        self.assertEqual(identifier.forgotten, identity)

    def test_multi_challenge_skipnomatch_findimplicit(self):
        environ = self._makeEnviron()
        app1 = DummyApp()
        app2 = DummyApp()
        from repoze.who.interfaces import IChallenger
        challenger1 = DummyChallenger(app1)
        challenger1.classifications = {IChallenger:['nomatch']}
        challenger2 = DummyChallenger(app2)
        challenger2.classifications = {IChallenger:None}
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        plugins = [ ('challenge1', challenger1), ('challenge2', challenger2) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                               [], identifier, identity)
        self.assertEqual(result, app2)
        self.assertEqual(environ['challenged'], app2)
        self.assertEqual(identifier.forgotten, identity)

    def test_multi_challenge_skipnomatch_findexplicit(self):
        environ = self._makeEnviron()
        app1 = DummyApp()
        app2 = DummyApp()
        from repoze.who.interfaces import IChallenger
        challenger1 = DummyChallenger(app1)
        challenger1.classifications = {IChallenger:['nomatch']}
        challenger2 = DummyChallenger(app2)
        challenger2.classifications = {IChallenger:['match']}
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        plugins = [ ('challenge1', challenger1), ('challenge2', challenger2) ]
        mw = self._makeOne(challengers = plugins)
        identity = {'login':'chris', 'password':'password'}
        result = mw.challenge(environ, 'match', '401 Unauthorized',
                               [], identifier, identity)
        self.assertEqual(result, app2)
        self.assertEqual(environ['challenged'], app2)
        self.assertEqual(identifier.forgotten, identity)

    def test_add_metadata(self):
        environ = self._makeEnviron()
        plugin1 = DummyMDProvider({'foo':'bar'})
        plugin2 = DummyMDProvider({'fuz':'baz'})
        plugins = [ ('meta1', plugin1), ('meta2', plugin2) ]
        mw = self._makeOne(mdproviders=plugins)
        classification = ''
        identity = {}
        results = mw.add_metadata(environ, classification, identity)
        self.assertEqual(identity['foo'], 'bar')
        self.assertEqual(identity['fuz'], 'baz')

    def test_add_metadata_w_classification(self):
        environ = self._makeEnviron()
        plugin1 = DummyMDProvider({'foo':'bar'})
        plugin2 = DummyMDProvider({'fuz':'baz'})
        from repoze.who.interfaces import IMetadataProvider
        plugin2.classifications = {IMetadataProvider:['foo']}
        plugins = [ ('meta1', plugin1), ('meta2', plugin2) ]
        mw = self._makeOne(mdproviders=plugins)
        classification = 'monkey'
        identity = {}
        mw.add_metadata(environ, classification, identity)
        self.assertEqual(identity['foo'], 'bar')
        self.assertEqual(identity.get('fuz'), None)

    def test_call_remoteuser_already_set(self):
        environ = self._makeEnviron({'REMOTE_USER':'admin'})
        mw = self._makeOne()
        result = mw(environ, None)
        self.assertEqual(mw.app.environ, environ)
        self.assertEqual(result, [])

    def test_call_200_no_plugins(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('200 OK', headers)
        mw = self._makeOne(app=app)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(mw.app.environ, environ)
        self.assertEqual(result, ['body'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, headers)

    def test_call_401_no_challengers(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('401 Unauthorized', headers)
        mw = self._makeOne(app=app)
        start_response = DummyStartResponse()
        self.assertRaises(RuntimeError, mw, environ, start_response)

    def test_call_200_no_challengers(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('200 OK', headers)
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        mw = self._makeOne(app=app, identifiers=identifiers)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(mw.app.environ, environ)
        self.assertEqual(result, ['body'])
        self.assertEqual(start_response.status, '200 OK')
        self.assertEqual(start_response.headers, headers)

    def test_call_401_no_identifiers(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('401 Unauthorized', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        mw = self._makeOne(app=app, challengers=challengers)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(environ['challenged'], challenge_app)
        self.failUnless(result[0].startswith('401 Unauthorized\r\n'))

    def test_call_401_challenger_and_identifier_no_authenticator(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('401 Unauthorized', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'a', 'password':'b'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers)
        start_response = DummyStartResponse()

        result = mw(environ, start_response)
        self.assertEqual(environ['challenged'], challenge_app)
        self.failUnless(result[0].startswith('401 Unauthorized\r\n'))
        self.assertEqual(identifier.forgotten, False)
        self.assertEqual(environ.get('REMOTE_USER'), None)

    def test_call_401_challenger_and_identifier_and_authenticator(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('401 Unauthorized', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(environ['challenged'], challenge_app)
        self.failUnless(result[0].startswith('401 Unauthorized\r\n'))
        # @@ unfuck
##         self.assertEqual(identifier.forgotten, identifier.credentials)
        self.assertEqual(environ['REMOTE_USER'], 'chris')
##         self.assertEqual(environ['repoze.who.identity'], identifier.credentials)

    def test_call_200_challenger_and_identifier_and_authenticator(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('200 OK', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(environ.get('challenged'), None)
        self.assertEqual(identifier.forgotten, False)
        # @@ figure out later
##         self.assertEqual(dict(identifier.remembered)['login'], dict(identifier.credentials)['login'])
##         self.assertEqual(dict(identifier.remembered)['password'], dict(identifier.credentials)['password'])
        self.assertEqual(environ['REMOTE_USER'], 'chris')
##         self.assertEqual(environ['repoze.who.identity'], identifier.credentials)


    def test_call_200_identity_reset(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        new_identity = {'user_id':'foo', 'password':'bar'}
        app = DummyIdentityResetApp('200 OK', headers, new_identity)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        self.assertEqual(environ.get('challenged'), None)
        self.assertEqual(identifier.forgotten, False)
        new_credentials = identifier.credentials.copy()
        new_credentials['login'] = 'fred'
        new_credentials['password'] = 'schooled'
        # @@ unfuck
##         self.assertEqual(identifier.remembered, new_credentials)
        self.assertEqual(environ['REMOTE_USER'], 'chris')
##         self.assertEqual(environ['repoze.who.identity'], new_credentials)

    def test_call_200_with_metadata(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('200 OK', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mdprovider = DummyMDProvider({'foo':'bar'})
        mdproviders = [ ('mdprovider', mdprovider) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators,
                           mdproviders=mdproviders)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        # metadata
        self.assertEqual(environ['repoze.who.identity']['foo'], 'bar')

    def test_call_ingress_plugin_replaces_application(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyWorkingApp('200 OK', headers)
        challengers = []
        credentials = {'login':'chris', 'password':'password'}
        from paste.httpexceptions import HTTPFound
        identifier = DummyIdentifier(
            credentials,
            remember_headers=[('a', '1')],
            replace_app = HTTPFound('http://example.com/redirect')
            )
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mdproviders = []
        mw = self._makeOne(app=app,
                           challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators,
                           mdproviders=mdproviders)
        start_response = DummyStartResponse()
        result = ''.join(mw(environ, start_response))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(start_response.status, '302 Found')
        headers = start_response.headers
        self.assertEqual(len(headers), 3)
        self.assertEqual(headers[0],
                         ('location', 'http://example.com/redirect'))
        self.assertEqual(headers[1],
                         ('content-type', 'text/plain; charset=utf8'))
        self.assertEqual(headers[2],
                         ('a', '1'))
        self.assertEqual(start_response.exc_info, None)
        self.failIf(environ.has_key('repoze.who.application'))

    def test_call_app_doesnt_call_start_response(self):
        environ = self._makeEnviron()
        headers = [('a', '1')]
        app = DummyGeneratorApp('200 OK', headers)
        from paste.httpexceptions import HTTPUnauthorized
        challenge_app = HTTPUnauthorized()
        challenge = DummyChallenger(challenge_app)
        challengers = [ ('challenge', challenge) ]
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)
        identifiers = [ ('identifier', identifier) ]
        authenticator = DummyAuthenticator()
        authenticators = [ ('authenticator', authenticator) ]
        mdprovider = DummyMDProvider({'foo':'bar'})
        mdproviders = [ ('mdprovider', mdprovider) ]
        mw = self._makeOne(app=app, challengers=challengers,
                           identifiers=identifiers,
                           authenticators=authenticators,
                           mdproviders=mdproviders)
        start_response = DummyStartResponse()
        result = mw(environ, start_response)
        # metadata
        self.assertEqual(environ['repoze.who.identity']['foo'], 'bar')

    # XXX need more call tests:
    #  - auth_id sorting

class TestMatchClassification(unittest.TestCase):

    def _getFUT(self):
        from repoze.who.middleware import match_classification
        return match_classification

    def test_match_classification(self):
        f = self._getFUT()
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IChallenger
        from repoze.who.interfaces import IAuthenticator
        multi1 = DummyMultiPlugin()
        multi2 = DummyMultiPlugin()
        multi1.classifications = {IIdentifier:('foo', 'bar'),
                                  IChallenger:('buz',),
                                  IAuthenticator:None}
        multi2.classifications = {IIdentifier:('foo', 'baz', 'biz')}
        plugins = (multi1, multi2)
        # specific
        self.assertEqual(f(IIdentifier, plugins, 'foo'), [multi1, multi2])
        self.assertEqual(f(IIdentifier, plugins, 'bar'), [multi1])
        self.assertEqual(f(IIdentifier, plugins, 'biz'), [multi2])
        # any for multi2
        self.assertEqual(f(IChallenger, plugins, 'buz'), [multi1, multi2])
        # any for either
        self.assertEqual(f(IAuthenticator, plugins, 'buz'), [multi1, multi2])

class TestStartResponseWrapper(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.middleware import StartResponseWrapper
        return StartResponseWrapper

    def _makeOne(self, *arg, **kw):
        plugin = self._getTargetClass()(*arg, **kw)
        return plugin

    def test_ctor(self):
        wrapper = self._makeOne(None)
        self.assertEqual(wrapper.start_response, None)
        self.assertEqual(wrapper.headers, [])
        self.failUnless(wrapper.buffer)

    def test_finish_response(self):
        statuses = []
        headerses = []
        datases = []
        closededs = []
        from StringIO import StringIO
        def write(data):
            datases.append(data)
        def close():
            closededs.append(True)
        write.close = close

        def start_response(status, headers, exc_info=None):
            statuses.append(status)
            headerses.append(headers)
            return write

        wrapper = self._makeOne(start_response)
        wrapper.status = '401 Unauthorized'
        wrapper.headers = [('a', '1')]
        wrapper.buffer = StringIO('written')
        extra_headers = [('b', '2')]
        result = wrapper.finish_response(extra_headers)
        self.assertEqual(result, None)
        self.assertEqual(headerses[0], wrapper.headers + extra_headers)
        self.assertEqual(statuses[0], wrapper.status)
        self.assertEqual(datases[0], 'written')
        self.assertEqual(closededs[0], True)

class TestMakeRegistries(unittest.TestCase):

    def _getFUT(self):
        from repoze.who.middleware import make_registries
        return make_registries

    def test_empty(self):
        fn = self._getFUT()
        iface_reg, name_reg = fn([], [], [], [])
        self.assertEqual(iface_reg, {})
        self.assertEqual(name_reg, {})

    def test_brokenimpl(self):
        fn = self._getFUT()
        self.assertRaises(ValueError, fn, [(None, DummyApp())], [], [], [])

    def test_ok(self):
        fn = self._getFUT()
        credentials1 = {'login':'chris', 'password':'password'}
        dummy_id1 = DummyIdentifier(credentials1)
        credentials2 = {'login':'chris', 'password':'password'}
        dummy_id2 = DummyIdentifier(credentials2)
        identifiers = [ ('id1', dummy_id1), ('id2', dummy_id2) ]
        dummy_auth = DummyAuthenticator(None)
        authenticators = [ ('auth', dummy_auth) ]
        dummy_challenger = DummyChallenger(None)
        challengers = [ ('challenger', dummy_challenger) ]
        dummy_mdprovider = DummyMDProvider()
        mdproviders = [ ('mdproviders', dummy_mdprovider) ]
        iface_reg, name_reg = fn(identifiers, authenticators, challengers,
                                 mdproviders)
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IAuthenticator
        from repoze.who.interfaces import IChallenger
        self.assertEqual(iface_reg[IIdentifier], [dummy_id1, dummy_id2])
        self.assertEqual(iface_reg[IAuthenticator], [dummy_auth])
        self.assertEqual(iface_reg[IChallenger], [dummy_challenger])
        self.assertEqual(name_reg['id1'], dummy_id1)
        self.assertEqual(name_reg['id2'], dummy_id2)
        self.assertEqual(name_reg['auth'], dummy_auth)
        self.assertEqual(name_reg['challenger'], dummy_challenger)

class TestIdentityDict(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.middleware import Identity
        return Identity

    def _makeOne(self, **kw):
        klass = self._getTargetClass()
        return klass(**kw)

    def test_str(self):
        identity = self._makeOne(foo=1)
        self.failUnless(str(identity).startswith('<repoze.who identity'))
        self.assertEqual(identity['foo'], 1)

    def test_repr(self):
        identity = self._makeOne(foo=1)
        self.failUnless(str(identity).startswith('<repoze.who identity'))
        self.assertEqual(identity['foo'], 1)

class WrapGeneratorTests(unittest.TestCase):

    def _getFUT(self):
        from repoze.who.middleware import wrap_generator
        return wrap_generator

    def test_it(self):
        L = []
        def gen(L=L):
            L.append('yo!')
            yield 'a'
            yield 'b'
        wrap_generator = self._getFUT()
        newgen = wrap_generator(gen())
        self.assertEqual(L, ['yo!'])
        self.assertEqual(list(newgen), ['a', 'b'])

class TestMakeTestMiddleware(unittest.TestCase):

    def setUp(self):
        import os
        self._old_WHO_LOG = os.environ.get('WHO_LOG')

    def tearDown(self):
        import os
        if self._old_WHO_LOG is not None:
            os.environ['WHO_LOG'] = self._old_WHO_LOG
        else:
            if 'WHO_LOG' in os.environ:
                del os.environ['WHO_LOG']

    def _getFactory(self):
        from repoze.who.middleware import make_test_middleware
        return make_test_middleware

    def test_it_no_WHO_LOG_in_environ(self):
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IAuthenticator
        from repoze.who.interfaces import IChallenger
        app = DummyApp()
        factory = self._getFactory()
        global_conf = {'here': '/'}
        middleware = factory(app, global_conf)
        self.assertEqual(len(middleware.registry[IIdentifier]), 3)
        self.assertEqual(len(middleware.registry[IAuthenticator]), 1)
        self.assertEqual(len(middleware.registry[IChallenger]), 2)
        self.assertEqual(middleware.logger, None)

    def test_it_w_WHO_LOG_in_environ(self):
        import logging
        import os
        os.environ['WHO_LOG'] = '1'
        app = DummyApp()
        factory = self._getFactory()
        global_conf = {'here': '/'}
        middleware = factory(app, global_conf)
        self.assertEqual(middleware.logger.getEffectiveLevel(), logging.DEBUG)

class DummyApp:
    environ = None
    def __call__(self, environ, start_response):
        self.environ = environ
        return []

class DummyWorkingApp:
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers

    def __call__(self, environ, start_response):
        self.environ = environ
        start_response(self.status, self.headers)
        return ['body']

class DummyGeneratorApp:
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers

    def __call__(self, environ, start_response):
        def gen(self=self, start_response=start_response):
            self.environ = environ
            start_response(self.status, self.headers)
            yield 'body'
        return gen()

class DummyIdentityResetApp:
    def __init__(self, status, headers, new_identity):
        self.status = status
        self.headers = headers
        self.new_identity = new_identity

    def __call__(self, environ, start_response):
        self.environ = environ
        environ['repoze.who.identity']['login'] = 'fred'
        environ['repoze.who.identity']['password'] = 'schooled'
        start_response(self.status, self.headers)
        return ['body']

class DummyChallenger:
    def __init__(self, app=None):
        self.app = app

    def challenge(self, environ, status, app_headers, forget_headers):
        environ['challenged'] = self.app
        return self.app

class DummyIdentifier:
    forgotten = False
    remembered = False

    def __init__(self, credentials=None, remember_headers=None,
                 forget_headers=None, replace_app=None):
        self.credentials = credentials
        self.remember_headers = remember_headers
        self.forget_headers = forget_headers
        self.replace_app = replace_app

    def identify(self, environ):
        if self.replace_app:
            environ['repoze.who.application'] = self.replace_app
        return self.credentials

    def forget(self, environ, identity):
        self.forgotten = identity
        return self.forget_headers

    def remember(self, environ, identity):
        self.remembered = identity
        return self.remember_headers

class DummyAuthenticator:
    def __init__(self, userid=None):
        self.userid = userid

    def authenticate(self, environ, credentials):
        if self.userid is None:
            return credentials['login']
        return self.userid

class DummyFailAuthenticator:
    def authenticate(self, environ, credentials):
        return None

class DummyRequestClassifier:
    def __call__(self, environ):
        return 'browser'

class DummyChallengeDecider:
    def __call__(self, environ, status, headers):
        if status.startswith('401 '):
            return True

class DummyNoResultsIdentifier:
    def identify(self, environ):
        return None

    def remember(self, *arg, **kw):
        pass

    def forget(self, *arg, **kw):
        pass

class DummyStartResponse:
    def __call__(self, status, headers, exc_info=None):
        self.status = status
        self.headers = headers
        self.exc_info = exc_info
        return []

class DummyMDProvider:
    def __init__(self, metadata=None):
        self._metadata = metadata

    def add_metadata(self, environ, identity):
        return identity.update(self._metadata)

class DummyMultiPlugin:
    pass
