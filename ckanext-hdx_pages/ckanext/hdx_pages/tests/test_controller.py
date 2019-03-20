'''
Created on March 19, 2019

@author: Dan


'''
import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import unicodedata
import ckan.lib.helpers as h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

page_elnino = {
    'name': 'elnino',
    'title': 'El Nino',
    'description': 'El Nino Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'groups': ['roger'],
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_elpico = {
    'name': 'elpico',
    'title': 'El Pico',
    'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'groups': ['roger'],
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_elgroupo = {
    'name': 'elgroupo',
    'title': 'El Groupo',
    'groups': ['roger'],
    'description': 'El Groupo Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}


class TestHDXControllerPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_pages hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXControllerPage, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_page_new(self):

        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        page_dict = self._get_action('page_create')(context_sysadmin, page_elnino)
        assert page_dict
        assert 'El Nino' in page_dict.get('description')
        assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')

        url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='new')
        try:
            self._get_url(url)
        except Exception, ex:
            assert '404 Not Found' in ex.message

        context['user'] = 'testsysadmin'
        user = model.User.by_name('testsysadmin')
        url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='new')
        page = self._get_url(url, user.apikey)
        assert '200' in page.status
        assert 'Save This Page' in page.body
        assert 'field_title' in page.body
        assert 'hdx_event_type' in page.body
        assert 'hdx_page_ongoing' in page.body
        assert 'field_name' in page.body

    def test_page_edit(self):

        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        page_dict = self._get_action('page_create')(context_sysadmin, page_elpico)
        assert page_dict
        assert 'El Pico' in page_dict.get('description')
        assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')

        url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='edit',
                        id=page_dict.get('id'))
        try:
            self._get_url(url)
        except Exception, ex:
            assert '404 Not Found' in ex.message

        context['user'] = 'testsysadmin'
        user = model.User.by_name('testsysadmin')
        url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='edit',
                        id=page_dict.get('id'))
        page = self._get_url(url, user.apikey)
        assert '200' in page.status
        assert 'Save This Page' in page.body
        assert 'field_title' in page.body
        assert 'hdx_event_type' in page.body
        assert 'hdx_page_ongoing' in page.body
        assert 'field_name' in page.body

    def _get_url(self, url, apikey=None):
        if apikey:
            page = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')})
        else:
            page = self.app.get(url)
        return page

    # def test_page_edit(self):
    #
    #     context = {'model': model, 'session': model.Session, 'user': 'tester'}
    #     context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
    #
    #     page_dict = self._get_action('page_create')(context_sysadmin, page_elpico)
    #     assert page_dict
    #     assert 'El Pico' in page_dict.get('description')
    #     assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')
    #
    #     user = model.User.by_name('testsysadmin')
    #     url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='edit',
    #                     id=page_dict.get('id'), extra_environ={'Authorization': 'testsysadmin'})
    #     response = self.app.get(url)
    #     assert '200' in response.status
    #
    #     user = model.User.by_name('tester')
    #     url = h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='edit',
    #                     id=page_dict.get('id'), extra_environ={'Authorization': 'tester'})
    #     response = self.app.get(url)
    #     assert '404' in response.status

