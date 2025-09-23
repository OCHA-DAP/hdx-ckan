import pytest
import logging
import ckan.lib.helpers as h
import mock
import ckan.model as model
from ckan.types import Context
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from ckanext.hdx_theme.tests.conftest import DATASET_NAME

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
log = logging.getLogger(__name__)

SYSADMIN = 'testsysadmin'

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'dataset_with_uploaded_resource')
class TestRequestTags(object):

    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_request_tags(self, mock_mail_recipient, app):
        factories.User(
            name=SYSADMIN,
            email='testsysadmin@hdx.hdxtest.org',
            sysadmin=True,
            fullname='Test Sysadmin',
            about='Just another Test Sysadmin test user.',
        )
        test_sysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']
        headers = {'Authorization': test_sysadmin_token}

        url = h.url_for('hdx_request_tags.request_tags')

        data = {
            'fullname': 'Test User',
            'email': 'testsysadmin@hdx.hdxtest.org',
        }
        result = app.post(url, headers=headers, data=data)
        assert result.json.get('success') is False

        data = {
            'fullname': 'Test User',
            'email': 'testsysadmin',
            'suggested_tags': 'new_tag',
            'datatype': 'Geospatial',
            'comment': 'This is a tag for testing',
        }
        result = app.post(url, headers=headers, data=data)
        assert result.json.get('success') is False


        data = {
            'fullname': 'Test User',
            'email': 'testsysadmin@hdx.hdxtest.org',
            'suggested_tags': 'new_tag,health,economics',
            'datatype': 'Geospatial',
            'comment': 'This is a tag for testing',
        }
        result = app.post(url, headers=headers, data=data)
        assert result.status_code == 200
        assert result.json.get('success') is False
        assert mock_mail_recipient.call_count == 0

        data = {
            'fullname': 'Test User',
            'email': 'testsysadmin@hdx.hdxtest.org',
            'suggested_tags': 'new_tag',
            'datatype': 'Geospatial',
            'comment': 'This is a tag for testing',
        }
        result = app.post(url, headers=headers, data=data)
        assert result.status_code == 200
        assert result.json.get('success')
        assert mock_mail_recipient.call_count == 1

    def test_dataset_old_links(self, app):

        url = h.url_for('hdx_dataset_old_links.new_notification_page')
        result = app.get(url)
        assert 'Please use the new contribute flow! This URL is no longer in use' in result.body
        assert result.status_code == 300

        url = h.url_for('hdx_dataset_old_links.edit_notification_page', id=DATASET_NAME)
        result = app.get(url)
        assert 'Please use the new contribute flow! This URL is no longer in use' in result.body
        assert result.status_code == 300

        url = h.url_for('hdx_dataset_old_links.resource_new_notification_page', id=DATASET_NAME)
        result = app.get(url)
        assert 'Please use the new contribute flow! This URL is no longer in use' in result.body
        assert result.status_code == 300

        url = h.url_for('hdx_dataset_old_links.resources_notification_page', id=DATASET_NAME)
        result = app.get(url)
        assert 'Please use the new contribute flow! This URL is no longer in use' in result.body
        assert result.status_code == 300

        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg_dict = _get_action('package_show')(sysadmin_context, {'id': DATASET_NAME})

        resource_id = pkg_dict.get('resources')[0].get('id') if pkg_dict.get('resources') else None
        url = h.url_for('hdx_dataset_old_links.resource_edit_notification_page', id=DATASET_NAME, resource_id=resource_id)
        result = app.get(url)
        assert 'Please use the new contribute flow! This URL is no longer in use' in result.body
        assert result.status_code == 300
