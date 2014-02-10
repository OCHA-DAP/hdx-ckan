import unittest
import StringIO

from repoze.who.tests import encode_multipart_formdata
from StringIO import StringIO

from repoze.who.plugins.openid.classifiers import openid_challenge_decider
from repoze.who.plugins.openid.identification import OpenIdIdentificationPlugin

from consumer import patch_plugin

class ChallengeTest(unittest.TestCase):
    """test the challenge plugin"""

    def setUp(self):
	self.server_response={
		"openid.mode"              : "id_res",
		"nonce"                    : "nonce",
		"openid.identity"          : "http://repoze.myopenid.com",
		"openid.assoc_handle"      : "assoc_handle",
		"openid.return_to"         : "return_to",
		"openid.signed"            : "signed",
		"openid.sig"               : "sig",
		"openid.invalidate_handle" : "invalidate_handle",
            }
	self.plugin = patch_plugin(OpenIdIdentificationPlugin(
					store = None,
					openid_field = 'repoze.whoplugins.openid.openid',
					error_field = '',
					store_file_path='',
					session_name = '',
					login_handler_path = '/login',
					logout_handler_path = '',
					login_form_url = '/login_form',
					logged_in_url = '',
					logged_out_url = '',
					came_from_field = 'came_from',
					rememberer_name = ''
					)
				    )

	environ = {'wsgi.input':'',
	    'wsgi.url_scheme': 'http',
	    'SERVER_NAME': 'localhost',
	    'SERVER_PORT': '8080',
	    'CONTENT_TYPE':'text/html',
	    'CONTENT_LENGTH':0,
	    'REQUEST_METHOD':'POST',
	    'PATH_INFO': '/protected',
	    'QUERY_STRING':'',
	}

        class DummyLogger:
            warnings = []
            debugs = []
            infos = []
            def warn(self, msg):
                self.warnings.append(msg)
            def debug(self, msg):
                self.debugs.append(msg)
            def info(self, msg):
                self.infos.append(msg)
        logger = environ['repoze.who.logger'] = DummyLogger()

	self.environ=environ

    def tearDown(self):
	pass

    def test_challenge_decider(self):
	"""test challenge decider"""

	environ = self.environ
	environ['repoze.whoplugins.openid.openid'] = 'foobar.com'

	# decider takes environ, status, headers
	self.assertEqual(openid_challenge_decider(environ, '200 Ok', {}), True)
	self.assertEqual(openid_challenge_decider({}, '401 Unauthorized', {}), True)
	self.assertEqual(openid_challenge_decider({}, '200 Ok', {}), False)

    def test_challenge_redirect(self):
	"""check if the challenge plugin works if given an openid"""

	# create a form POST response as if we would post the openid
	fields = [('repoze.whoplugins.openid.openid','foobar.com')]
	content_type, body = encode_multipart_formdata(fields)

	environ = self.environ
	environ['wsgi.input'] = StringIO(body)
	environ['REQUEST_METHOD'] = 'POST'
	environ['CONTENT_LENGTH'] = len(body)
	environ['CONTENT_TYPE'] = content_type

	# in this case the plugin has to redirect to the openid provider
	# faked by MockConsumer in this case
	res = self.plugin.challenge(environ, '200 Ok', {}, {})
	self.assertEqual(res.location,'http://someopenidprovider.com/somewhere')
	self.assertEqual(res.status,'302 Found')

    def test_challenge_show_login_form(self):
	"""test if the challenge plugin redirects to the login form"""

	res = self.plugin.challenge(self.environ, '200 Ok', {}, {})
	self.assertEqual(res.location,'/login_form?came_from=http://localhost:8080/protected')
	self.assertEqual(res.status,'302 Found')

    def test_login_form_send(self):
	"""test if the login form data is received and the environment set correctly"""
	fields = [('repoze.whoplugins.openid.openid','foobar.com')]
	content_type, body = encode_multipart_formdata(fields)

	environ = self.environ
	environ['wsgi.input'] = StringIO(body)
	environ['REQUEST_METHOD'] = 'POST'
	environ['CONTENT_LENGTH'] = len(body)
	environ['CONTENT_TYPE'] = content_type
	environ['PATH_INFO'] = '/login'

	identity = self.plugin.identify(environ)
	self.assertEqual(environ.get('repoze.whoplugins.openid.openid',None), 'foobar.com')

    def test_complete_openid_request(self):
	"""test if the openid request completes"""

	environ = self.environ
	environ['PATH_INFO'] = '/login'

	fields = self.server_response.items()
	content_type, body = encode_multipart_formdata(fields)
	environ['wsgi.input'] = StringIO(body)
	environ['REQUEST_METHOD'] = 'POST'
	environ['CONTENT_LENGTH'] = len(body)
	environ['CONTENT_TYPE'] = content_type
	
	identity = self.plugin.identify(environ)
	self.assertEqual(identity['repoze.who.plugins.openid.userid'],'http://repoze.myopenid.com')

    def test_incomplete_openid_request(self):
	"""test if the openid request fails with a wrong identity"""

	environ = self.environ
	environ['PATH_INFO'] = '/login'

	sresp = self.server_response
	sresp['openid.identity'] = ''

	fields = sresp.items()
	content_type, body = encode_multipart_formdata(fields)
	environ['wsgi.input'] = StringIO(body)
	environ['REQUEST_METHOD'] = 'POST'
	environ['CONTENT_LENGTH'] = len(body)
	environ['CONTENT_TYPE'] = content_type
	
	identity = self.plugin.identify(environ)
	self.assertEqual(identity.get('repoze.who.plugins.openid.userid',None),None)

    def test_authenticate(self):
	"""test if the authentication plugin works as well"""
	environ = self.environ
	identity = {'repoze.who.plugins.openid.userid' : 'http://foobar.com'}
	res = self.plugin.authenticate(environ, identity)
	self.assertEqual(res, 'http://foobar.com')
