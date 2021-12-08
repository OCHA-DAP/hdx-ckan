'''
Created on March 19, 2019

@author: Dan


'''
import pytest
import six
import ckan.model as model
import ckan.plugins.toolkit as tk
import logging as logging
import ckan.logic as logic

from ckanext.hdx_dataviz.tests import USER, SYSADMIN, ORG, LOCATION
import unicodedata
import ckan.lib.helpers as h

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized

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

page_elpico = {
    'name': 'elpico',
    'title': 'El Pico',
    'description': 'El Pico Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'groups': [LOCATION],
    'state': 'active',
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

page_dashbo = {
    'name': 'eldashbo',
    'title': 'El Dashbo',
    'groups': [LOCATION],
    'description': 'El Dashbo Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'dashboards',
    'status': 'archived',
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

page_eldeleted = {
    'name': 'eldeleted',
    'title': 'El Deleted',
    'groups': [LOCATION],
    'description': 'El Deleted Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.',
    'type': 'event',
    'status': 'ongoing',
    'state': 'active',
    'sections': '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}

class TestHDXControllerPage(object):

    def _get_url(self, app, url, apikey=None):

        if apikey:
            page = app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apikey).encode('ascii', 'ignore')}, follow_redirects=True)
        else:
            page = app.get(url)
        return page


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestHDXControllerPageNew(TestHDXControllerPage):

    @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    @pytest.mark.usefixtures('with_request_context')
    def test_page_new(self, app):

        context = {'model': model, 'session': model.Session, 'user': USER}
        # context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        url = h.url_for('hdx_custom_page.new')
        try:
            page_new = self._get_url(app, url)
            assert 'Page not found' in page_new.body, 'a regular user can not not access a page creation form'
            assert '404 Not Found'.lower() in page_new.status.lower()
        except Exception as ex:
            assert False

        context['user'] = SYSADMIN
        user = model.User.by_name(SYSADMIN)
        # url = h.url_for('hdx_custom_page.new')
        page = self._get_url(app, url, user.apikey)
        assert '200' in page.status
        assert 'Save This Page' in page.body
        assert 'field_title' in page.body
        assert 'hdx_event_type' in page.body
        assert 'hdx_page_ongoing' in page.body
        assert 'field_name' in page.body


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestHDXControllerPageEdit(TestHDXControllerPage):

    @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    def test_page_edit(self, app):

        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        page_dict = _get_action('page_create')(context_sysadmin, page_elpico)
        assert page_dict
        assert 'El Pico' in page_dict.get('title')
        assert 'Lorem Ipsum is simply dummy text' in page_dict.get('description')

        url = h.url_for(u'hdx_custom_page.edit', id=page_dict.get('id'))
        try:
            page_edit = self._get_url(app, url)
            assert 'Page not found' in page_edit.body, 'a regular user can not not access a page edit form'
            assert '404 Not Found'.lower() in page_edit.status.lower()
        except Exception as ex:
            assert False

        context['user'] = SYSADMIN
        user = model.User.by_name(SYSADMIN)
        url = h.url_for(u'hdx_custom_page.edit', id=page_dict.get('id'))
        page = self._get_url(app, url, user.apikey)
        assert '200' in page.status
        assert 'Save This Page' in page.body
        assert 'field_title' in page.body
        assert 'hdx_event_type' in page.body
        assert 'hdx_page_ongoing' in page.body
        assert 'field_name' in page.body


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data',
                         'with_request_context')
class TestHDXControllerPageRead(TestHDXControllerPage):

    @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    def test_page_read(self, app):

        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        elnino = _get_action('page_create')(context_sysadmin, page_elnino)
        assert elnino
        assert 'El Nino' in elnino.get('description')
        assert 'Lorem Ipsum is simply dummy text' in elnino.get('description')

        eldashbo = _get_action('page_create')(context_sysadmin, page_dashbo)
        assert eldashbo
        assert 'El Dashbo' in eldashbo.get('description')
        assert 'Lorem Ipsum is simply dummy text' in eldashbo.get('description')

        context['user'] = SYSADMIN
        user = model.User.by_name(SYSADMIN)
        url = h.url_for(u'hdx_event.read_event', id=elnino.get('id'))

        elnino_result = self._get_url(app, url, user.apikey)
        assert '200' in elnino_result.status

        url = h.url_for(u'hdx_dashboard.read_dashboard', id=eldashbo.get('id'))
        eldashbo_result = self._get_url(app, url, user.apikey)
        assert '200' in eldashbo_result.status

        try:
            url = h.url_for(u'hdx_event.read_event', id='nopageid')
            eldashbo_result = self._get_url(app, url, user.apikey)
            assert 'Page not found' in eldashbo_result.body, 'page doesn\'t exist'
            assert '404 Not Found'.lower() in eldashbo_result.status.lower()
        except Exception as ex:
            assert False


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestHDXControllerPageDelete(TestHDXControllerPage):

    @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    def test_page_delete(self, app):

        context = {'model': model, 'session': model.Session, 'user': USER}
        context_sysadmin = {'model': model, 'session': model.Session, 'user': SYSADMIN}

        try:
            eldeleted_dict = _get_action('page_create')(context_sysadmin, page_eldeleted)
            assert eldeleted_dict
            assert 'El Deleted' in eldeleted_dict.get('title')
            assert 'eldeleted' in eldeleted_dict.get('name')
            assert 'El Deleted Lorem Ipsum' in eldeleted_dict.get('description')
        except Exception as ex:
            assert False

        eldeleted_page = _get_action('page_show')(context_sysadmin, {'id': page_eldeleted.get('name')})
        user = model.User.by_name(USER)
        try:
            url = h.url_for(u'hdx_custom_page.delete_page', id=eldeleted_page.get('id'))
            page_delete = app.post(url, extra_environ={"REMOTE_USER": USER})
            assert 'Page not found' in page_delete.body, 'page doesn\'t exist'
            assert '404 Not Found'.lower() in page_delete.status.lower()
        except logic.NotAuthorized:
            assert False
        except Exception as ex:
            log.info(ex)
            assert False

        context['user'] = SYSADMIN
        sysadmin = model.User.by_name(SYSADMIN)

        try:
            url = h.url_for(u'hdx_custom_page.delete_page', id='nopageid')
            page_delete = self._get_url(app, url, sysadmin.apikey)
            assert 'Page not found' in page_delete.body, 'page doesn\'t exist'
            assert '404 NOT FOUND'.lower() in page_delete.status.lower()
        except Exception as ex:
            assert False

        context['user'] = SYSADMIN
        try:
            _url = h.url_for(u'hdx_custom_page.delete_page', id=eldeleted_page.get('id'))
            res = app.post(_url, environ_overrides={"REMOTE_USER": SYSADMIN}, follow_redirects=False)
            assert '302 FOUND'.lower() in res.status.lower()
            _res = _get_action('page_show')(context_sysadmin, {'id': page_eldeleted.get('name')})
            assert False
        except logic.NotFound:
            assert True
        except Exception as ex:
            assert False
