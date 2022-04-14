import pytest
import six
import unicodedata
import mock

import ckan.model as model
import ckan.lib.helpers as h

import ckanext.hdx_users.model as umodel
import ckanext.hdx_user_extra.model as ue_model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.mock_helper as mh
import ckanext.hdx_theme.helpers.faq_wordpress as fw


contact_form = {
    'topic': 'Getting Started',
    'fullname': 'hdx',
    'email': 'hdx.feedback@gmail.com',
    'faq-mesg': 'my question',
}


# @pytest.mark.skipif(six.PY3, reason=u"The user_extras plugin is not available on PY3 yet")
class TestFaqPageController(hdx_test_base.HdxBaseTest):

    # loads missing plugins
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def setup_class(cls):
        super(TestFaqPageController, cls).setup_class()
        umodel.setup()
        ue_model.create_table()

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_faq_contact_us(self, mocked_mail_recipient):

        try:
            res = self.app.post('/faq/contact_us', params=contact_form)
        except Exception as ex:
            assert False
        assert '200 OK' in res.status
        assert "success" in res.body and "true" in res.body
        assert True

    def test_resulting_page(self):
        testsysadmin = model.User.by_name('testsysadmin')

        # /faqs/licenses
        _old_faq_for_category = fw.faq_for_category
        fw.faq_for_category = mh.mock_faqs_license_page_content
        page = self._get_faqs_page('licenses')
        assert 'Data Licenses' in page.body, 'the url /faqs/license should redirect to the Data Licenses page when no user is logged in'
        page = self._get_faqs_page('licenses', testsysadmin.apikey)
        assert 'Data Licenses' in page.body, 'the url /faqs/license should redirect to the Data Licenses page, even when the user is logged in'
        fw.faq_for_category = _old_faq_for_category

        # /faqs/terms
        _old_faq_for_category = fw.faq_for_category
        fw.faq_for_category = mh.mock_faqs_terms_page_content
        page = self._get_faqs_page('terms')
        assert 'HDX Terms of Service' in page.body, 'the url /faqs/terms should redirect to the Terms of Service page when no user is logged in'
        assert 'HDX is an open platform and anyone can use it without creating a user account.' in page.body, 'the url /faqs/terms should redirect to the Terms of Service page when no user is logged in'
        page = self._get_faqs_page('terms', testsysadmin.apikey)
        assert 'HDX Terms of Service' in page.body, 'the url /faqs/terms should redirect to the Terms of Service page, even when the user is logged in'
        fw.faq_for_category = _old_faq_for_category

        # /about/hdx-qa-process
        page = self._get_about_page('hdx-qa-process')
        assert 'Responsible Data Sharing on HDX' in page.body, 'the url /about/hdx-qa-proces should redirect to the QA process page when no user is logged in'
        page = self._get_about_page('hdx-qa-process', testsysadmin.apikey)
        assert 'Responsible Data Sharing on HDX' in page.body, 'the url /about/hdx-qa-proces should redirect to the QA process page, even when the user is logged in'

        page = self._get_about_page('fake')
        assert page.status_code == 404

        page = self._get_about_page('fake', testsysadmin.apikey)
        assert page.status_code == 404

    def test_faq_page(self):
        testsysadmin = model.User.by_name('testsysadmin')

        _old_get_post = fw.faq_for_category
        fw.faq_for_category = mh.mock_faq_page_content
        url = '/faq'
        page = self._get_url_page(url)
        assert 'Frequently Asked Questions' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        assert 'FAQ' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        page = self._get_url_page(url, testsysadmin.apikey)
        assert 'Frequently Asked Questions' in page.body, 'the url /faqs/licenses should redirect to the FAQ page, even when the user is logged in'
        fw.faq_for_category = _old_get_post

    def _get_faqs_page(self, page, apikey=None):
        # global pages
        test_client = self.get_backwards_compatible_test_client()
        #url = '/faqs/' + page
        url = h.url_for('hdx_faqs.read', category=page)
        if apikey:
            page = test_client.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = test_client.get(url)
        return page

    def _get_about_page(self, page, apikey=None):
        # global pages
        test_client = self.get_backwards_compatible_test_client()
        url = '/about/' + page
        if apikey:
            page = test_client.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = test_client.get(url)
        return page

    # Resources for developers
    def test_documentation_page(self):
        testsysadmin = model.User.by_name('testsysadmin')

        _old_get_post = fw.faq_for_category
        fw.faq_for_category = mh.mock_documentation_page_content
        page = self._get_faqs_page('devs')
        assert 'Resources for Developers' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        assert 'Accessing HDX by API' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        page = self._get_faqs_page('devs', testsysadmin.apikey)
        assert 'Resources for Developers' in page.body, 'the url /faqs/licenses should redirect to the FAQ page, even when the user is logged in'
        fw.faq_for_category = _old_get_post

    def test_data_responsability_page(self):
        testsysadmin = model.User.by_name('testsysadmin')

        _old_get_post = fw.faq_for_category
        fw.faq_for_category = mh.mock_data_responsability_page_content
        # url = h.url_for(controller='ckanext.hdx_theme.controllers.faq_data_responsibility:FaqDataResponsibilityController', action='show')
        page = self._get_faqs_page('covid')
        assert 'Data Responsibility in the COVID-19 Response' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        assert 'About Data Responsibility for COVID-19' in page.body, 'the url /faq should redirect to the FAQ page when no user is logged in'
        page = self._get_faqs_page('covid', testsysadmin.apikey)
        assert 'Data Responsibility in the COVID-19 Response' in page.body, 'the url /faqs/licenses should redirect to the FAQ page, even when the user is logged in'
        fw.faq_for_category = _old_get_post

    def _get_url_page(self, url, apikey=None):
        # global pages
        test_client = self.get_backwards_compatible_test_client()
        if apikey:
            page = test_client.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = test_client.get(url)
        return page
