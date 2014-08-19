import ckan.logic as logic
import ckan.model as model
import unicodedata

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


class TestAboutPageController(hdx_test_base.HdxBaseTest):
    
    #loads missing plugins
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('register hdx_theme')

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


