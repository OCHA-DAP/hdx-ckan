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

    @staticmethod
    def _get_page_post_param():

        return {
            'name': 'elnino',
            'title': 'El Nino Lorem Ipsum',
            'description': 'El Nino Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
            'type': 'event',
            'status': 'ongoing',
            'state': 'active',
            'save_custom_page': 'active',
            'hdx_counter': '2',
            'groups': ['roger'],
            'field_section_0_data_url': 'https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21',
            'field_section_0_max_height': '350px',
            'field_section_0_section_title': 'El Nino Affected Countries',
            'field_section_0_type': 'map',
            'field_section_1_data_url': 'https://data.humdata.local/search?q=el%20nino',
            'field_section_1_section_title': 'Data',
            'field_section_1_type': 'data_list',
            'hdx_page_id': ''
        }

    def test_page_create(self):
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        user = model.User.by_name('tester')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

        post_params = self._get_page_post_param()

        try:
            res = self.app.post('/page/new', params=post_params, extra_environ=auth)
            assert False
        except Exception, ex:
            assert '404 Not Found' in ex.message

        user = model.User.by_name('testsysadmin')
        user.email = 'test@test.com'
        auth = {'Authorization': str(user.apikey)}

        # post_params = self._get_page_post_param()

        try:
            res = self.app.post('/page/new', params=post_params, extra_environ=auth)
        except Exception, ex:
            assert False
        assert '302' in res.status
        assert '/event/elnino' in res.body

        elnino = self._get_action('page_show')(context, {'id': 'elnino'})
        assert elnino
        assert 'El Nino Lorem Ipsum' in elnino.get('title')
        assert 'elnino' in elnino.get('name')

        del post_params['name']
        try:
            res = self.app.post('/page/new', params=post_params, extra_environ=auth)
        except Exception, ex:
            assert True
