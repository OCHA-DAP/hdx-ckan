import unittest

class TestWhoConfig(unittest.TestCase):

    def _getTargetClass(self):
        from repoze.who.config import WhoConfig
        return WhoConfig

    def _makeOne(self, here='/', *args, **kw):
        return self._getTargetClass()(here, *args, **kw)

    def _getDummyPluginClass(self, iface):
        from zope.interface import classImplements
        if not iface.implementedBy(DummyPlugin):
            classImplements(DummyPlugin, iface)
        return DummyPlugin

    def test_defaults_before_parse(self):
        config = self._makeOne()
        self.assertEqual(config.request_classifier, None)
        self.assertEqual(config.challenge_decider, None)
        self.assertEqual(config.remote_user_key, 'REMOTE_USER')
        self.assertEqual(len(config.plugins), 0)
        self.assertEqual(len(config.identifiers), 0)
        self.assertEqual(len(config.authenticators), 0)
        self.assertEqual(len(config.challengers), 0)
        self.assertEqual(len(config.mdproviders), 0)

    def test_parse_empty_string(self):
        config = self._makeOne()
        config.parse('')
        self.assertEqual(config.request_classifier, None)
        self.assertEqual(config.challenge_decider, None)
        self.assertEqual(config.remote_user_key, 'REMOTE_USER')
        self.assertEqual(len(config.plugins), 0)
        self.assertEqual(len(config.identifiers), 0)
        self.assertEqual(len(config.authenticators), 0)
        self.assertEqual(len(config.challengers), 0)
        self.assertEqual(len(config.mdproviders), 0)

    def test_parse_empty_file(self):
        from StringIO import StringIO
        config = self._makeOne()
        config.parse(StringIO())
        self.assertEqual(config.request_classifier, None)
        self.assertEqual(config.challenge_decider, None)
        self.assertEqual(config.remote_user_key, 'REMOTE_USER')
        self.assertEqual(len(config.plugins), 0)
        self.assertEqual(len(config.identifiers), 0)
        self.assertEqual(len(config.authenticators), 0)
        self.assertEqual(len(config.challengers), 0)
        self.assertEqual(len(config.mdproviders), 0)

    def test_parse_plugins(self):
        config = self._makeOne()
        config.parse(PLUGINS_ONLY)
        self.assertEqual(len(config.plugins), 2)
        self.failUnless(isinstance(config.plugins['foo'],
                                   DummyPlugin))
        bar = config.plugins['bar']
        self.failUnless(isinstance(bar, DummyPlugin))
        self.assertEqual(bar.credentials, 'qux')

    def test_parse_general_empty(self):
        config = self._makeOne()
        config.parse('[general]')
        self.assertEqual(config.request_classifier, None)
        self.assertEqual(config.challenge_decider, None)
        self.assertEqual(config.remote_user_key, 'REMOTE_USER')
        self.assertEqual(len(config.plugins), 0)

    def test_parse_general_only(self):
        from repoze.who.interfaces import IRequestClassifier
        from repoze.who.interfaces import IChallengeDecider
        class IDummy(IRequestClassifier, IChallengeDecider):
            pass
        PLUGIN_CLASS = self._getDummyPluginClass(IDummy)
        config = self._makeOne()
        config.parse(GENERAL_ONLY)
        self.failUnless(isinstance(config.request_classifier, PLUGIN_CLASS))
        self.failUnless(isinstance(config.challenge_decider, PLUGIN_CLASS))
        self.assertEqual(config.remote_user_key, 'ANOTHER_REMOTE_USER')
        self.assertEqual(len(config.plugins), 0)

    def test_parse_general_with_plugins(self):
        from repoze.who.interfaces import IRequestClassifier
        from repoze.who.interfaces import IChallengeDecider
        class IDummy(IRequestClassifier, IChallengeDecider):
            pass
        PLUGIN_CLASS = self._getDummyPluginClass(IDummy)
        config = self._makeOne()
        config.parse(GENERAL_WITH_PLUGINS)
        self.failUnless(isinstance(config.request_classifier, PLUGIN_CLASS))
        self.failUnless(isinstance(config.challenge_decider, PLUGIN_CLASS))

    def test_parse_identifiers_only(self):
        from repoze.who.interfaces import IIdentifier
        PLUGIN_CLASS = self._getDummyPluginClass(IIdentifier)
        config = self._makeOne()
        config.parse(IDENTIFIERS_ONLY)
        identifiers = config.identifiers
        self.assertEqual(len(identifiers), 2)
        first, second = identifiers
        self.assertEqual(first[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IIdentifier], 'klass1')
        self.assertEqual(second[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_identifiers_with_plugins(self):
        from repoze.who.interfaces import IIdentifier
        PLUGIN_CLASS = self._getDummyPluginClass(IIdentifier)
        config = self._makeOne()
        config.parse(IDENTIFIERS_WITH_PLUGINS)
        identifiers = config.identifiers
        self.assertEqual(len(identifiers), 2)
        first, second = identifiers
        self.assertEqual(first[0], 'foo')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IIdentifier], 'klass1')
        self.assertEqual(second[0], 'bar')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_authenticators_only(self):
        from repoze.who.interfaces import IAuthenticator
        PLUGIN_CLASS = self._getDummyPluginClass(IAuthenticator)
        config = self._makeOne()
        config.parse(AUTHENTICATORS_ONLY)
        authenticators = config.authenticators
        self.assertEqual(len(authenticators), 2)
        first, second = authenticators
        self.assertEqual(first[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IAuthenticator], 'klass1')
        self.assertEqual(second[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_authenticators_with_plugins(self):
        from repoze.who.interfaces import IAuthenticator
        PLUGIN_CLASS = self._getDummyPluginClass(IAuthenticator)
        config = self._makeOne()
        config.parse(AUTHENTICATORS_WITH_PLUGINS)
        authenticators = config.authenticators
        self.assertEqual(len(authenticators), 2)
        first, second = authenticators
        self.assertEqual(first[0], 'foo')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IAuthenticator], 'klass1')
        self.assertEqual(second[0], 'bar')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_challengers_only(self):
        from repoze.who.interfaces import IChallenger
        PLUGIN_CLASS = self._getDummyPluginClass(IChallenger)
        config = self._makeOne()
        config.parse(CHALLENGERS_ONLY)
        challengers = config.challengers
        self.assertEqual(len(challengers), 2)
        first, second = challengers
        self.assertEqual(first[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IChallenger], 'klass1')
        self.assertEqual(second[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_challengers_with_plugins(self):
        from repoze.who.interfaces import IChallenger
        PLUGIN_CLASS = self._getDummyPluginClass(IChallenger)
        config = self._makeOne()
        config.parse(CHALLENGERS_WITH_PLUGINS)
        challengers = config.challengers
        self.assertEqual(len(challengers), 2)
        first, second = challengers
        self.assertEqual(first[0], 'foo')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IChallenger], 'klass1')
        self.assertEqual(second[0], 'bar')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_mdproviders_only(self):
        from repoze.who.interfaces import IMetadataProvider
        PLUGIN_CLASS = self._getDummyPluginClass(IMetadataProvider)
        config = self._makeOne()
        config.parse(MDPROVIDERS_ONLY)
        mdproviders = config.mdproviders
        self.assertEqual(len(mdproviders), 2)
        first, second = mdproviders
        self.assertEqual(first[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IMetadataProvider], 'klass1')
        self.assertEqual(second[0], 'repoze.who.tests.test_config:DummyPlugin')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_mdproviders_with_plugins(self):
        from repoze.who.interfaces import IMetadataProvider
        PLUGIN_CLASS = self._getDummyPluginClass(IMetadataProvider)
        config = self._makeOne()
        config.parse(MDPROVIDERS_WITH_PLUGINS)
        mdproviders = config.mdproviders
        self.assertEqual(len(mdproviders), 2)
        first, second = mdproviders
        self.assertEqual(first[0], 'foo')
        self.failUnless(isinstance(first[1], PLUGIN_CLASS))
        self.assertEqual(len(first[1].classifications), 1)
        self.assertEqual(first[1].classifications[IMetadataProvider], 'klass1')
        self.assertEqual(second[0], 'bar')
        self.failUnless(isinstance(second[1], PLUGIN_CLASS))

    def test_parse_make_plugin_names(self):
        # see http://bugs.repoze.org/issue92
        config = self._makeOne()
        config.parse(MAKE_PLUGIN_ARG_NAMES)
        self.assertEqual(len(config.plugins), 1)
        foo = config.plugins['foo']
        self.failUnless(isinstance(foo, DummyPlugin))
        self.assertEqual(foo.iface, 'iface')
        self.assertEqual(foo.name, 'name')

class DummyPlugin:
    def __init__(self, **kw):
        self.__dict__.update(kw)

PLUGINS_ONLY = """\
[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:bar]
use = repoze.who.tests.test_config:DummyPlugin
credentials = qux
"""

GENERAL_ONLY = """\
[general]
request_classifier = repoze.who.tests.test_config:DummyPlugin
challenge_decider = repoze.who.tests.test_config:DummyPlugin
remote_user_key = ANOTHER_REMOTE_USER
"""

GENERAL_WITH_PLUGINS = """\
[general]
request_classifier = classifier
challenge_decider = decider

[plugin:classifier]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:decider]
use = repoze.who.tests.test_config:DummyPlugin
"""

IDENTIFIERS_ONLY = """\
[identifiers]
plugins =
    repoze.who.tests.test_config:DummyPlugin;klass1
    repoze.who.tests.test_config:DummyPlugin
"""

IDENTIFIERS_WITH_PLUGINS = """\
[identifiers]
plugins =
    foo;klass1
    bar

[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:bar]
use = repoze.who.tests.test_config:DummyPlugin
"""

AUTHENTICATORS_ONLY = """\
[authenticators]
plugins =
    repoze.who.tests.test_config:DummyPlugin;klass1
    repoze.who.tests.test_config:DummyPlugin
"""

AUTHENTICATORS_WITH_PLUGINS = """\
[authenticators]
plugins =
    foo;klass1
    bar

[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:bar]
use = repoze.who.tests.test_config:DummyPlugin
"""

CHALLENGERS_ONLY = """\
[challengers]
plugins =
    repoze.who.tests.test_config:DummyPlugin;klass1
    repoze.who.tests.test_config:DummyPlugin
"""

CHALLENGERS_WITH_PLUGINS = """\
[challengers]
plugins =
    foo;klass1
    bar

[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:bar]
use = repoze.who.tests.test_config:DummyPlugin
"""

MDPROVIDERS_ONLY = """\
[mdproviders]
plugins =
    repoze.who.tests.test_config:DummyPlugin;klass1
    repoze.who.tests.test_config:DummyPlugin
"""

MDPROVIDERS_WITH_PLUGINS = """\
[mdproviders]
plugins =
    foo;klass1
    bar

[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin

[plugin:bar]
use = repoze.who.tests.test_config:DummyPlugin
"""

MAKE_PLUGIN_ARG_NAMES = """\
[plugin:foo]
use = repoze.who.tests.test_config:DummyPlugin
name = name
iface = iface
"""

class TestConfigMiddleware(unittest.TestCase):
    tempdir = None

    def setUp(self):
        pass

    def tearDown(self):
        if self.tempdir is not None:
            import shutil
            shutil.rmtree(self.tempdir)

    def _getFactory(self):
        from repoze.who.config import make_middleware_with_config
        return make_middleware_with_config

    def _getTempfile(self, text):
        import os
        import tempfile
        tempdir = self.tempdir = tempfile.mkdtemp()
        path = os.path.join(tempdir, 'who.ini')
        config = open(path, 'w')
        config.write(text)
        config.flush()
        config.close()
        return path

    def test_sample_config(self):
        import logging
        from repoze.who.interfaces import IIdentifier
        from repoze.who.interfaces import IAuthenticator
        from repoze.who.interfaces import IChallenger
        app = DummyApp()
        factory = self._getFactory()
        path = self._getTempfile(SAMPLE_CONFIG)
        global_conf = {'here': '/'}
        middleware = factory(app, global_conf, config_file=path,
                             log_file='STDOUT', log_level='debug')
        self.assertEqual(len(middleware.registry[IIdentifier]), 3)
        self.assertEqual(len(middleware.registry[IAuthenticator]), 1)
        self.assertEqual(len(middleware.registry[IChallenger]), 2)
        self.failUnless(middleware.logger, middleware.logger)
        self.assertEqual(middleware.logger.getEffectiveLevel(), logging.DEBUG)

    def test_sample_config_no_log_level(self):
        import logging
        app = DummyApp()
        factory = self._getFactory()
        path = self._getTempfile(SAMPLE_CONFIG)
        global_conf = {'here': '/'}
        middleware = factory(app, global_conf, config_file=path,
                             log_file='STDOUT')
        self.assertEqual(middleware.logger.getEffectiveLevel(), logging.INFO)

    def test_sample_config_w_log_file(self):
        import logging
        import os
        app = DummyApp()
        factory = self._getFactory()
        path = self._getTempfile(SAMPLE_CONFIG)
        logfile = os.path.join(self.tempdir, 'who.log')
        global_conf = {'here': '/'}
        middleware = factory(app, global_conf, config_file=path,
                             log_file=logfile)
        self.assertEqual(middleware.logger.getEffectiveLevel(), logging.INFO)
        logging.shutdown()

SAMPLE_CONFIG = """\
[plugin:form]
use = repoze.who.plugins.form:make_plugin
login_form_qs = __do_login
rememberer_name = auth_tkt

[plugin:auth_tkt]
use = repoze.who.plugins.auth_tkt:make_plugin
secret = s33kr1t
cookie_name = oatmeal
secure = False
include_ip = True

[plugin:basicauth]
use = repoze.who.plugins.basicauth:make_plugin
realm = 'sample'

[plugin:htpasswd]
use = repoze.who.plugins.htpasswd:make_plugin
filename = %(here)s/etc/passwd
check_fn = repoze.who.plugins.htpasswd:crypt_check

[general]
request_classifier = repoze.who.classifiers:default_request_classifier
challenge_decider = repoze.who.classifiers:default_challenge_decider

[identifiers]
plugins =
    form;browser
    auth_tkt
    basicauth

[authenticators]
plugins = htpasswd

[challengers]
plugins =
    form;browser
    basicauth

[mdproviders]
plugins =

"""

class DummyApp:
    environ = None
    def __call__(self, environ, start_response):
        self.environ = environ
        return []


