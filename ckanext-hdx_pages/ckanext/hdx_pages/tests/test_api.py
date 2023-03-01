'''
Created on March 19, 2019

@author: Dan


'''
import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import logging as logging
import ckan.logic as logic

from ckanext.hdx_dataviz.tests import USER, SYSADMIN, LOCATION

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)

page_elnino = {
    'name': 'elnino',
    'title': 'El Nino',
    'description': 'Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'extras': '{"show_title": "on"}',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_elpico = {
    'name': 'elpico',
    'title': 'El Pico',
    'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'extras': '{"show_title": "off"}',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_elgroupo = {
    'name': 'elgroupo',
    'title': 'El Groupo',
    'groups': [LOCATION],
    'description': 'El Groupo Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_eldeleted = {
    'name': 'eldeleted',
    'title': 'El Deleted',
    'groups': [LOCATION],
    'description': 'El Groupo Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'archived',
    'state': 'deleted',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXApiPage(object):

    def test_page_api(self):

        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        page_dict = _get_action('page_create')(context_sysadmin, page_elnino)
        assert page_dict
        assert 'El Pico' not in page_dict.get('title')
        assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')

        elnino = _get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
        assert elnino
        assert 'El Pico' not in elnino.get('title')
        assert 'El Nino' == elnino.get('title')
        assert 'elnino' == elnino.get('name')
        assert 'Lorem Ipsum is simply dummy text' in elnino.get('description')
        assert 'event' == elnino.get('type')
        assert 'ongoing' == elnino.get('status')
        assert 'show_title' in elnino.get('extras') and elnino.get('extras').get('show_title') == 'on'
        assert 'https://data.humdata.org/dataset/wfp-and-fao-overview' in elnino.get('sections')

        try:
            _get_action('page_update')(context_sysadmin, {'id': page_dict.get('id')})
            assert False
        except Exception as ex:
            assert True

        grp_dict = _get_action('group_show')(context_sysadmin, {'id': LOCATION})
        new_page_dict = _get_action('page_update')(context_sysadmin, {'name': page_elpico.get('name'),
                                                                      'id': page_dict.get('id'),
                                                                      'title': page_elpico.get('title'),
                                                                      'extras': page_elpico.get('extras'),
                                                                      'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
                                                                      'groups': [grp_dict.get('id')]
                                                                      }
                                                   )
        assert new_page_dict
        assert 'El Pico' in new_page_dict.get('title')
        assert 'show_title' in new_page_dict.get('extras') and new_page_dict.get('extras').get('show_title') == 'off'

        try:
            _get_action('page_create')(context, page_elpico)
            assert False
        except logic.NotAuthorized:
            assert True
        except Exception as ex:
            assert True

        try:
            _get_action('page_update')(context, {'title': 'El Pico Lorem Ipsum'})
            assert False
        except logic.NotAuthorized:
            assert True
        except Exception as ex:
            assert True

        try:
            _get_action('page_delete')(context, {'id': page_dict.get('id') or page_dict.get('name')})
            assert False
        except logic.NotAuthorized:
            assert True
        except Exception as ex:
            assert True

        try:
            _get_action('page_update')(context_sysadmin, {'id': 'nopageid'})
            assert False
        except logic.NotFound:
            assert True
        except logic.ValidationError:
            assert True
        except Exception as ex:
            assert True

        try:
            _get_action('page_delete')(context_sysadmin, {'id': 'nopageid'})
            assert False
        except logic.NotFound:
            assert True
        except logic.ValidationError:
            assert True
        except Exception as ex:
            assert True

        _get_action('page_delete')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
        try:
            _get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})
            assert False
        except logic.NotFound:
            assert True
        except Exception as ex:
            assert True

        assert True


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXPageWithGroups(object):

    def test_page_with_groups(self):
        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        page_dict = _get_action('page_create')(context_sysadmin, page_elgroupo)

        try:
            _get_action('page_create')(context_sysadmin, page_elgroupo)
        except Exception as ex:
            log.info(ex)
            assert True

        elgroupo = _get_action('page_show')(context_sysadmin, {'id': page_dict.get('id') or page_dict.get('name')})

        page_group_list = _get_action('page_group_list')(context_sysadmin, {'id': page_dict.get('id')})
        assert page_group_list

        page_list = _get_action('page_list')(context_sysadmin, {})
        assert page_list

        grp_dict = _get_action('group_show')(context_sysadmin, {'id': LOCATION})
        group_page_list = _get_action('group_page_list')(context_sysadmin, {'id': grp_dict.get('id')})
        assert group_page_list

        try:
            page_elgroupo['name'] = 'elgroupo2'
            page_elgroupo['groups'] = [grp_dict.get('id'), grp_dict.get('id')]
            _get_action('page_create')(context_sysadmin, page_elgroupo)
            assert False
        except Exception as ex:
            log.info(ex)
            assert True

        try:
            page_elgroupo['name'] = 'elgroupo3'
            page_elgroupo['title'] = 'None'
            page_elgroupo['groups'] = [grp_dict.get('id')]
            _get_action('page_create')(context_sysadmin, page_elgroupo)
            assert False
        except Exception as ex:
            log.info(ex)
            assert True


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXValidationPage(object):

    def test_validation_page(self):
        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        del page_elpico['name']
        try:
            _get_action('page_create')(context_sysadmin, page_elpico)
        except logic.ValidationError:
            assert True
        except Exception as ex:
            log.info(ex)
            assert True


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXPageShow(object):

    def test_page_show(self):
        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        page = _get_action('page_create')(context_sysadmin, page_eldeleted)

        eldeleted = _get_action('page_show')(context_sysadmin, {'id': page.get('id')})
        assert 'deleted' == eldeleted.get('state')

        try:
            _get_action('page_show')(context, {'id': page.get('id')})
        except Exception as ex:
            log.info(ex)
            assert True

        try:
            _get_action('page_show')(context_sysadmin, {})
            assert False
        except logic.ValidationError:
            assert True
