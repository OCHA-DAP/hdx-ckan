'''
Created on March 19, 2019

@author: Dan


'''
import logging as logging
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)

page_elnino = {
    'name': 'elnino',
    'title': 'El Nino',
    'description': 'Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_elpico = {
    'name': 'elpico',
    'title': 'El Pico',
    'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
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


class TestHDXApiPage(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

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
        super(TestHDXApiPage, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_page_api(self):

        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        page_dict = self._get_action('page_create')(context_sysadmin, page_elnino)
        assert page_dict
        assert 'El Pico' not in page_dict.get('description')
        assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')

        elnino = self._get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
        assert elnino
        assert 'El Pico' not in elnino.get('description')
        assert 'El Nino' == elnino.get('title')
        assert 'elnino' == elnino.get('name')
        assert 'Lorem Ipsum is simply dummy text' in elnino.get('description')
        assert 'event' == elnino.get('type')
        assert 'ongoing' == elnino.get('status')
        assert 'https://data.humdata.org/dataset/wfp-and-fao-overview' in elnino.get('sections')


        new_page_dict = self._get_action('page_update')(context_sysadmin, {'name': page_dict.get('name'),
                                                                           'id': page_dict.get('id'),
                                                                           'title': page_dict.get('title'),
                                                                           'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.'})
        assert new_page_dict
        assert 'El Pico' in new_page_dict.get('description')

        try:
            self._get_action('page_create')(context, page_elpico)
        except logic.NotAuthorized:
            assert True

        try:
            self._get_action('page_update')(context, {'description': 'El Pico Lorem Ipsum'})
        except logic.NotAuthorized:
            assert True

        try:
            self._get_action('page_delete')(context, {'id': page_dict.get('id') or page_dict.get('name')})
        except logic.NotAuthorized:
            assert True

        self._get_action('page_delete')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
        try:
            self._get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
        except logic.NotFound:
            assert True

        assert True

    def test_page_with_groups(self):
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        page_dict = self._get_action('page_create')(context_sysadmin, page_elgroupo)

        try:
            self._get_action('page_create')(context_sysadmin, page_elgroupo)
        except Exception, ex:
            log.info(ex)
            assert True

        elgroupo = self._get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})

        page_group_list = self._get_action('page_group_list')(context_sysadmin, {'id': page_dict.get('id')})
        assert page_group_list

        page_list = self._get_action('page_list')(context_sysadmin, {})
        assert page_list

        grp_dict = self._get_action('group_show')(context_sysadmin, {'id':'roger'})
        group_page_list = self._get_action('group_page_list')(context_sysadmin, {'id': grp_dict.get('id')})
        assert group_page_list

        try:
            page_elgroupo['name'] = 'elgroupo2'
            page_elgroupo['groups'] = [grp_dict.get('id'), grp_dict.get('id')]
            self._get_action('page_create')(context_sysadmin, page_elgroupo)
        except Exception, ex:
            log.info(ex)
            assert True

        try:
            page_elgroupo['name'] = 'elgroupo3'
            page_elgroupo['title'] = 'None'
            page_elgroupo['groups'] = [grp_dict.get('id')]
            self._get_action('page_create')(context_sysadmin, page_elgroupo)
        except Exception, ex:
            log.info(ex)
            assert True

    def test_page_with_groups(self):
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        page_elpico['name'] = None
        try:
            self._get_action('page_create')(context_sysadmin, page_elpico)
        except logic.ValidationError:
            assert True
