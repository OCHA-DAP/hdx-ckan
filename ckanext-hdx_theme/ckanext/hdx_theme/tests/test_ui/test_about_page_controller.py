import ckan
import ckan.logic as logic
import ckan.tests as tests
import webtest
import ckan.lib.helpers as h
import ckan.lib.create_test_data as ctd
import ckan.lib.search as search
import ckan.model as model
import unicodedata
from ckan.config.middleware import make_app
from pylons import config

def _get_test_app():
    config['ckan.legacy_templates'] = False
    app = ckan.config.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app

def _load_plugin(plugin):
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)

class TestAboutPageController(object):

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()

        _load_plugin('hdx_theme')
        cls.app = _get_test_app()

        search.clear()
        model.Session.remove()
        ctd.CreateTestData.create()



    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()

        config.clear()
        config.update(cls.original_config)

    def test_resulting_page(self):
        testsysadmin = model.User.by_name('testsysadmin')

        page = self._getAboutPage('license')
        assert 'Data Licenses' in str(page.response), 'the url /about/license should redirect to the Data Licenses page when no user is logged in'
        page = self._getAboutPage('license', testsysadmin.apikey)
        assert 'Data Licenses' in str(page.response), 'the url /about/license should redirect to the Data Licenses page, even when the user is logged in'

        page = self._getAboutPage('terms')
        assert 'Terms of Service' in str(page.response), 'the url /about/terms should redirect to the Terms of Service page when no user is logged in'
        page = self._getAboutPage('terms', testsysadmin.apikey)
        assert 'Terms of Service' in str(page.response), 'the url /about/terms should redirect to the Terms of Service page, even when the user is logged in'

        try:
            page = self._getAboutPage('fake')
            assert "The requested about page doesn't exist" in str(page.response), 'the url /about/fake should throw an error when no user is logged in'
        except logic.ValidationError:
            assert True

        try:
            page = self._getAboutPage('fake', testsysadmin.apikey)
            assert "The requested about page doesn't exist" in str(page.response), 'the url /about/terms should throw an error, even when the user is logged in'
        except logic.ValidationError:
            assert True


    def _getAboutPage(self, page, apikey=None):
        url = '/about/' + page
        if apikey:
            page = self.app.get(url,headers={'Authorization':unicodedata.normalize('NFKD', apikey).encode('ascii','ignore')})
        else:
            page = self.app.get(url)
        return page


