import unittest

class TestFormPlugin(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.plugins.form import FormPlugin
        return FormPlugin

    def _makeOne(self,
                 login_form_qs='__do_login',
                 rememberer_name='cookie',
                 formbody=None,
                 formcallable=None,
                ):
        plugin = self._getTargetClass()(login_form_qs, rememberer_name,
                                        formbody, formcallable)
        return plugin

    def _makeEnviron(self, login=None, password=None, do_login=False,
                     max_age=None):
        from StringIO import StringIO
        fields = []
        if login:
            fields.append(('login', login))
        if password:
            fields.append(('password', password))
        if max_age:
            fields.append(('max_age', max_age))
        content_type, body = encode_multipart_formdata(fields)
        credentials = {'login':'chris', 'password':'password'}
        identifier = DummyIdentifier(credentials)

        environ = {'wsgi.version': (1,0),
                   'wsgi.input': StringIO(body),
                   'wsgi.url_scheme': 'http',
                   'SERVER_NAME': 'localhost',
                   'SERVER_PORT': '8080',
                   'CONTENT_TYPE': content_type,
                   'CONTENT_LENGTH': len(body),
                   'REQUEST_METHOD': 'POST',
                   'repoze.who.plugins': {'cookie':identifier},
                   'PATH_INFO': '/protected',
                   'QUERY_STRING': '',
                  }
        if do_login:
            environ['QUERY_STRING'] = '__do_login=true'
        return environ
    
    def test_implements(self):
        from zope.interface.verify import verifyClass
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IChallenger
        klass = self._getTargetClass()
        verifyClass(IIdentifier, klass)
        verifyClass(IChallenger, klass)

    def test_identify_noqs(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        
    def test_identify_qs_no_values(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(do_login=True)
        result = plugin.identify(environ)
        self.assertEqual(result, None)

    def test_identify_nologin(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(do_login=True, login='chris')
        result = plugin.identify(environ)
        self.assertEqual(result, None)
    
    def test_identify_nopassword(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(do_login=True, password='password')
        result = plugin.identify(environ)
        self.assertEqual(result, None)

    def test_identify_success(self):
        from paste.httpexceptions import HTTPFound
        plugin = self._makeOne()
        environ = self._makeEnviron(do_login=True, login='chris',
                                        password='password')
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password'})
        app = environ['repoze.who.application']
        self.failUnless(isinstance(app, HTTPFound))
        self.assertEqual(app.location(), 'http://localhost:8080/protected')

    def test_identify_success_with_max_age(self):
        from paste.httpexceptions import HTTPFound
        plugin = self._makeOne()
        environ = self._makeEnviron(do_login=True, login='chris',
                                        password='password', max_age='500')
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password',
                                  'max_age':'500'})
        app = environ['repoze.who.application']
        self.failUnless(isinstance(app, HTTPFound))
        self.assertEqual(app.location(), 'http://localhost:8080/protected')

    def test_remember(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        identity = {}
        result = plugin.remember(environ, identity)
        self.assertEqual(result, None)
        self.assertEqual(environ['repoze.who.plugins']['cookie'].remembered,
                         identity)

    def test_forget(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        identity = {}
        result = plugin.forget(environ, identity)
        self.assertEqual(result, None)
        self.assertEqual(environ['repoze.who.plugins']['cookie'].forgotten,
                         identity
                         )

    def test_challenge_defaultform(self):
        from repoze.who.plugins.form import _DEFAULT_FORM
        plugin = self._makeOne()
        environ = self._makeEnviron()
        app = plugin.challenge(environ, '401 Unauthorized', [], [])
        sr = DummyStartResponse()
        result = app(environ, sr)
        self.assertEqual(''.join(result), _DEFAULT_FORM)
        self.assertEqual(len(sr.headers), 2)
        cl = str(len(_DEFAULT_FORM))
        self.assertEqual(sr.headers[0], ('Content-Length', cl))
        self.assertEqual(sr.headers[1], ('Content-Type', 'text/html'))
        self.assertEqual(sr.status, '200 OK')

    def test_challenge_customform(self):
        import os
        here = os.path.dirname(__file__)
        fixtures = os.path.join(here, 'fixtures')
        form = os.path.join(fixtures, 'form.html')
        formbody = open(form).read()
        plugin = self._makeOne(formbody=formbody)
        environ = self._makeEnviron()
        app = plugin.challenge(environ, '401 Unauthorized', [], [])
        sr = DummyStartResponse()
        result = app(environ, sr)
        self.assertEqual(''.join(result), formbody)
        self.assertEqual(len(sr.headers), 2)
        cl = str(len(formbody))
        self.assertEqual(sr.headers[0], ('Content-Length', cl))
        self.assertEqual(sr.headers[1], ('Content-Type', 'text/html'))
        self.assertEqual(sr.status, '200 OK')

    def test_challenge_formcallable(self):
        def _formcallable(environ):
            return 'formcallable'
        plugin = self._makeOne(formcallable=_formcallable)
        environ = self._makeEnviron()
        app = plugin.challenge(environ, '401 Unauthorized', [], [])
        sr = DummyStartResponse()
        result = app(environ, sr)
        self.assertEqual(result, ['formcallable'])

    def test_challenge_with_location(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        app = plugin.challenge(environ, '401 Unauthorized',
                               [('Location', 'http://foo/bar')],
                               [('Set-Cookie', 'a=123')])
        sr = DummyStartResponse()
        app(environ, sr)
        headers = sorted(sr.headers)
        self.assertEqual(len(headers), 3)
        self.assertEqual(headers[0], ('Location', 'http://foo/bar'))
        self.assertEqual(headers[1],
                         ('Set-Cookie', 'a=123'))
        self.assertEqual(headers[2],
                         ('content-type', 'text/plain; charset=utf8'))
        self.assertEqual(sr.status, '302 Found')

class Test_make_plugin(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from repoze.who.plugins.form import make_plugin
        return make_plugin(*args, **kw)

    def test_no_rememberer_name_raises(self):
        self.assertRaises(ValueError, self._callFUT)

    def test_with_form(self):
        import os
        here = os.path.dirname(__file__)
        fixtures = os.path.join(here, 'fixtures')
        form = os.path.join(fixtures, 'form.html')
        formbody = open(form).read()
        plugin = self._callFUT('__login', 'cookie', form)
        self.assertEqual(plugin.login_form_qs, '__login')
        self.assertEqual(plugin.rememberer_name, 'cookie')
        self.assertEqual(plugin.formbody, formbody)
        self.assertEqual(plugin.formcallable, None)

    def test_default_form(self):
        plugin = self._callFUT('__login', 'cookie')
        self.assertEqual(plugin.login_form_qs, '__login')
        self.assertEqual(plugin.rememberer_name, 'cookie')
        self.assertEqual(plugin.formbody, None)
        self.assertEqual(plugin.formcallable, None)

    def test_with_formcallable(self):
        dotted='repoze.who.plugins.tests.test_form:sample_formcallable'
        plugin = self._callFUT('__login', 'cookie', 
                               formcallable=dotted
                               )
        self.assertEqual(plugin.formcallable, sample_formcallable)

def sample_formcallable(environ):
    return {'foo': 'bar'}


class TestRedirectingFormPlugin(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.plugins.form import RedirectingFormPlugin
        return RedirectingFormPlugin

    def _makeOne(self, login_form_url='http://example.com/login.html',
                 login_handler_path = '/login_handler',
                 logout_handler_path = '/logout_handler',
                 rememberer_name='cookie',
                 reason_param='reason'):
        plugin = self._getTargetClass()(login_form_url, login_handler_path,
                                        logout_handler_path,
                                        rememberer_name, reason_param)
        return plugin

    def _makeEnviron(self, login=None, password=None, came_from=None,
                         path_info='/', identifier=None, max_age=None):
        from StringIO import StringIO
        fields = []
        if login:
            fields.append(('login', login))
        if password:
            fields.append(('password', password))
        if came_from:
            fields.append(('came_from', came_from))
        if max_age:
            fields.append(('max_age', max_age))
        if identifier is None:
            credentials = {'login':'chris', 'password':'password'}
            identifier = DummyIdentifier(credentials)
        content_type, body = encode_multipart_formdata(fields)
        environ = {'wsgi.version': (1,0),
                   'wsgi.input': StringIO(body),
                   'wsgi.url_scheme':'http',
                   'SERVER_NAME': 'www.example.com',
                   'SERVER_PORT': '80',
                   'CONTENT_TYPE': content_type,
                   'CONTENT_LENGTH': len(body),
                   'REQUEST_METHOD': 'POST',
                   'repoze.who.plugins': {'cookie':identifier},
                   'QUERY_STRING': 'default=1',
                   'PATH_INFO': path_info,
                  }
        return environ
    
    def test_implements(self):
        from zope.interface.verify import verifyClass
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IChallenger
        klass = self._getTargetClass()
        verifyClass(IIdentifier, klass)
        verifyClass(IChallenger, klass)

    def test_identify_pathinfo_miss(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/not_login_handler')
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        self.failIf(environ.get('repoze.who.application'))
        
    def test_identify_via_login_handler(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/login_handler',
                                        login='chris',
                                        password='password',
                                        came_from='http://example.com')
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password'})
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 1)
        name, value = app.headers[0]
        self.assertEqual(name, 'location')
        self.assertEqual(value, 'http://example.com')
        self.assertEqual(app.code, 302)

    def test_identify_via_login_handler_max_age(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/login_handler',
                                    login='chris',
                                    password='password',
                                    came_from='http://example.com',
                                    max_age='500')
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password',
                                  'max_age':'500'})
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 1)
        name, value = app.headers[0]
        self.assertEqual(name, 'location')
        self.assertEqual(value, 'http://example.com')
        self.assertEqual(app.code, 302)

    def test_identify_via_login_handler_no_username_pass(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/login_handler')
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 1)
        name, value = app.headers[0]
        self.assertEqual(name, 'location')
        self.assertEqual(value, '/')
        self.assertEqual(app.code, 302)

    def test_identify_via_login_handler_no_came_from_no_http_referer(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/login_handler',
                                        login='chris',
                                        password='password')
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password'})
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 1)
        name, value = app.headers[0]
        self.assertEqual(name, 'location')
        self.assertEqual(value, '/')
        self.assertEqual(app.code, 302)

    def test_identify_via_login_handler_no_came_from(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/login_handler',
                                        login='chris',
                                        password='password')
        environ['HTTP_REFERER'] = 'http://foo.bar'
        result = plugin.identify(environ)
        self.assertEqual(result, {'login':'chris', 'password':'password'})
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 1)
        name, value = app.headers[0]
        self.assertEqual(name, 'location')
        self.assertEqual(value, 'http://foo.bar')
        self.assertEqual(app.code, 302)

    def test_identify_via_logout_handler(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/logout_handler',
                                        login='chris',
                                        password='password',
                                        came_from='http://example.com')
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 0)
        self.assertEqual(app.code, 401)
        self.assertEqual(environ['came_from'], 'http://example.com')

    def test_identify_via_logout_handler_no_came_from_no_http_referer(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/logout_handler',
                                        login='chris',
                                        password='password')
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 0)
        self.assertEqual(app.code, 401)
        self.assertEqual(environ['came_from'], '/')

    def test_identify_via_logout_handler_no_came_from(self):
        plugin = self._makeOne()
        environ = self._makeEnviron(path_info='/logout_handler',
                                        login='chris',
                                        password='password')
        environ['HTTP_REFERER'] = 'http://example.com/referer'
        result = plugin.identify(environ)
        self.assertEqual(result, None)
        app = environ['repoze.who.application']
        self.assertEqual(len(app.headers), 0)
        self.assertEqual(app.code, 401)
        self.assertEqual(environ['came_from'], 'http://example.com/referer')

    def test_remember(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        identity = {}
        result = plugin.remember(environ, identity)
        self.assertEqual(result, None)
        self.assertEqual(environ['repoze.who.plugins']['cookie'].remembered,
                         identity)

    def test_forget(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        identity = {}
        result = plugin.forget(environ, identity)
        self.assertEqual(result, None)
        self.assertEqual(environ['repoze.who.plugins']['cookie'].forgotten,
                         identity
                         )

    def test_challenge(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        app = plugin.challenge(environ, '401 Unauthorized', [('app', '1')],
                               [('forget', '1')])
        sr = DummyStartResponse()
        result = ''.join(app(environ, sr))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(len(sr.headers), 3)
        self.assertEqual(sr.headers[0][0], 'Location')
        url = sr.headers[0][1]
        import urlparse
        import cgi
        parts = urlparse.urlparse(url)
        parts_qsl = cgi.parse_qsl(parts[4])
        self.assertEqual(len(parts_qsl), 1)
        came_from_key, came_from_value = parts_qsl[0]
        self.assertEqual(parts[0], 'http')
        self.assertEqual(parts[1], 'example.com')
        self.assertEqual(parts[2], '/login.html')
        self.assertEqual(parts[3], '')
        self.assertEqual(came_from_key, 'came_from')
        self.assertEqual(came_from_value, 'http://www.example.com/?default=1')
        headers = sr.headers
        self.assertEqual(len(headers), 3)
        self.assertEqual(sr.headers[1][0], 'forget')
        self.assertEqual(sr.headers[1][1], '1')
        self.assertEqual(sr.headers[2][0], 'content-type')
        self.assertEqual(sr.headers[2][1], 'text/plain; charset=utf8')
        self.assertEqual(sr.status, '302 Found')

    def test_challenge_came_from_in_environ(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        environ['came_from'] = 'http://example.com/came_from'
        app = plugin.challenge(environ, '401 Unauthorized', [('app', '1')],
                               [('forget', '1')])
        sr = DummyStartResponse()
        result = ''.join(app(environ, sr))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(len(sr.headers), 3)
        self.assertEqual(sr.headers[0][0], 'Location')
        url = sr.headers[0][1]
        import urlparse
        import cgi
        parts = urlparse.urlparse(url)
        parts_qsl = cgi.parse_qsl(parts[4])
        self.assertEqual(len(parts_qsl), 1)
        came_from_key, came_from_value = parts_qsl[0]
        self.assertEqual(parts[0], 'http')
        self.assertEqual(parts[1], 'example.com')
        self.assertEqual(parts[2], '/login.html')
        self.assertEqual(parts[3], '')
        self.assertEqual(came_from_key, 'came_from')
        self.assertEqual(came_from_value, 'http://example.com/came_from')

    def test_challenge_with_reason_header(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        environ['came_from'] = 'http://example.com/came_from'
        app = plugin.challenge(
            environ, '401 Unauthorized',
            [('X-Authorization-Failure-Reason', 'you are ugly')],
            [('forget', '1')])
        sr = DummyStartResponse()
        result = ''.join(app(environ, sr))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(len(sr.headers), 3)
        self.assertEqual(sr.headers[0][0], 'Location')
        url = sr.headers[0][1]
        import urlparse
        import cgi
        parts = urlparse.urlparse(url)
        parts_qsl = cgi.parse_qsl(parts[4])
        self.assertEqual(len(parts_qsl), 2)
        parts_qsl.sort()
        came_from_key, came_from_value = parts_qsl[0]
        reason_key, reason_value = parts_qsl[1]
        self.assertEqual(parts[0], 'http')
        self.assertEqual(parts[1], 'example.com')
        self.assertEqual(parts[2], '/login.html')
        self.assertEqual(parts[3], '')
        self.assertEqual(came_from_key, 'came_from')
        self.assertEqual(came_from_value, 'http://example.com/came_from')
        self.assertEqual(reason_key, 'reason')
        self.assertEqual(reason_value, 'you are ugly')

    def test_challenge_with_reason_and_custom_reason_param(self):
        plugin = self._makeOne(reason_param='auth_failure')
        environ = self._makeEnviron()
        environ['came_from'] = 'http://example.com/came_from'
        app = plugin.challenge(
            environ, '401 Unauthorized',
            [('X-Authorization-Failure-Reason', 'you are ugly')],
            [('forget', '1')])
        sr = DummyStartResponse()
        result = ''.join(app(environ, sr))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(len(sr.headers), 3)
        self.assertEqual(sr.headers[0][0], 'Location')
        url = sr.headers[0][1]
        import urlparse
        import cgi
        parts = urlparse.urlparse(url)
        parts_qsl = cgi.parse_qsl(parts[4])
        self.assertEqual(len(parts_qsl), 2)
        parts_qsl.sort()
        reason_key, reason_value = parts_qsl[0]
        came_from_key, came_from_value = parts_qsl[1]
        self.assertEqual(parts[0], 'http')
        self.assertEqual(parts[1], 'example.com')
        self.assertEqual(parts[2], '/login.html')
        self.assertEqual(parts[3], '')
        self.assertEqual(came_from_key, 'came_from')
        self.assertEqual(came_from_value, 'http://example.com/came_from')
        self.assertEqual(reason_key, 'auth_failure')
        self.assertEqual(reason_value, 'you are ugly')

    def test_challenge_with_setcookie_from_app(self):
        plugin = self._makeOne()
        environ = self._makeEnviron()
        app = plugin.challenge(
            environ,
            '401 Unauthorized',
            [('app', '1'), ('set-cookie','a'), ('set-cookie','b')],
            [])
        sr = DummyStartResponse()
        result = ''.join(app(environ, sr))
        self.failUnless(result.startswith('302 Found'))
        self.assertEqual(sr.headers[1][0], 'set-cookie')
        self.assertEqual(sr.headers[1][1], 'a')
        self.assertEqual(sr.headers[2][0], 'set-cookie')
        self.assertEqual(sr.headers[2][1], 'b')

class Test_make_redirecting_plugin(unittest.TestCase):

    def _callFUT(self, *args, **kw):
        from repoze.who.plugins.form import make_redirecting_plugin
        return make_redirecting_plugin(*args, **kw)

    def test_factory_no_login_form_url_raises(self):
        self.assertRaises(ValueError, self._callFUT, None)

    def test_factory_no_login_handler_path_raises(self):
        self.assertRaises(ValueError, self._callFUT, '/go_there', None)

    def test_factory_no_logout_handler_path_raises(self):
        self.assertRaises(ValueError, self._callFUT,
                          '/go_there', '/logged_in', None)

    def test_factory_no_rememberer_name_raises(self):
        self.assertRaises(ValueError, self._callFUT,
                          '/go_there', '/logged_in', '/logged_out', None)

    def test_factory_ok(self):
        plugin = self._callFUT('/go_there',
                               '/logged_in',
                               '/logged_out',
                               'rememberer')
        self.assertEqual(plugin.login_form_url, '/go_there')
        self.assertEqual(plugin.login_handler_path, '/logged_in')
        self.assertEqual(plugin.logout_handler_path, '/logged_out')
        self.assertEqual(plugin.rememberer_name, 'rememberer')

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

class DummyStartResponse:
    def __call__(self, status, headers, exc_info=None):
        self.status = status
        self.headers = headers
        self.exc_info = exc_info
        return []

def encode_multipart_formdata(fields):
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\r\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body
