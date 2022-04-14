'''
Created on March 19, 2019

@author: Dan


'''
import pytest
import six
import ckan.model as model
import logging as logging
import ckan.logic as logic

from ckanext.hdx_dataviz.tests import USER, SYSADMIN, LOCATION
from ckan.lib.helpers import url_for

_get_action = logic.get_action
NotAuthorized = logic.NotAuthorized

log = logging.getLogger(__name__)

page_elnino = {
    'name': 'elnino',
    'title': 'El Nino',
    'description': 'El Nino Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'groups': [LOCATION],
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXPageController(object):


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
            'groups': [LOCATION],
            'field_section_0_data_url': 'https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21',
            'field_section_0_max_height': '350px',
            'field_section_0_section_title': 'El Nino Affected Countries',
            'field_section_0_type': 'map',
            'field_section_1_data_url': 'https://data.humdata.local/search?q=el%20nino',
            'field_section_1_section_title': 'Data',
            'field_section_1_type': 'data_list',
            'hdx_page_id': ''
        }

    # @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    def test_page_create(self, app):
        context = {'model': model, 'session': model.Session, 'user': USER}

        user = model.User.by_name(USER)
        auth = {'Authorization': str(user.apikey)}
        url = url_for(u'hdx_custom_page.new')
        post_params = self._get_page_post_param()

        try:
            res = app.post(url, data=post_params, extra_environ={"REMOTE_USER": USER})
            assert 'Page not found' in res.body
        except Exception as ex:
            assert False

        user = model.User.by_name(SYSADMIN)

        try:
            res = app.post(url, data=post_params, environ_overrides={"REMOTE_USER": SYSADMIN}, follow_redirects=False)
            assert True
        except Exception as ex:
            assert False
        assert '302 FOUND' in res.status

        elnino = _get_action('page_show')(context, {'id': 'elnino'})
        assert elnino
        assert 'El Nino Lorem Ipsum' in elnino.get('title')
        assert 'elnino' in elnino.get('name')

        del post_params['name']
        try:
            res = app.post(url, data=post_params, environ_overrides={"REMOTE_USER": SYSADMIN}, follow_redirects=False)
            assert 'Page name cannot be empty' in res.body
        except Exception as ex:
            assert False
