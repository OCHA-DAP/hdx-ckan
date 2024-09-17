import mock
import pytest
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

get_action = tk.get_action
config = tk.config
h = tk.h

USER_NAME = 'test_user'
USER_EMAIL = 'test_user@test.org'
SYSADMIN_NAME = 'sysadmin_user'
SYSADMIN_EMAIL = 'sysadmin_user@test.org'
ORGANIZATION_NAME = 'test_organization'
LOCATION_NAME = 'test_location'
REQUEST_ACCESS_DATASET_NAME = 'request_access_test_dataset'
PUBLIC_DATASET_NAME = 'public_test_dataset'
PRIVATE_DATASET_NAME = 'private_test_dataset'
CONST_REQUEST_ACCESS = h.HDX_CONST('UI_CONSTANTS')['REQUEST_ACCESS']
CONST_SIGNIN = h.HDX_CONST('UI_CONSTANTS')['SIGNIN']


@pytest.fixture()
def setup_data():
    factories.Sysadmin(name=SYSADMIN_NAME, email=SYSADMIN_EMAIL, fullname='Sysadmin User')
    factories.User(name=USER_NAME, email=USER_EMAIL, fullname='Test User')
    factories.Organization(
        name=ORGANIZATION_NAME,
        title='Test Organization',
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )
    factories.Group(name=LOCATION_NAME)


def get_sysadmin_context():
    return {'model': model, 'user': SYSADMIN_NAME}


def get_user_context():
    return {'model': model, 'user': USER_NAME}


@pytest.mark.usefixtures('clean_db', 'clean_index', 'setup_data')
class TestRequestAccessView(object):
    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_request_access(self, mock_mail_recipient, app):
        user_token = factories.APIToken(user=USER_NAME, expires_in=2, unit=60 * 60)['token']
        auth_headers = {'Authorization': user_token}

        package = {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '[1960-01-01 TO 2012-12-31]',
            'indicator': '0',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'Test data',
            'license_id': 'hdx-other',
            'name': REQUEST_ACCESS_DATASET_NAME,
            'notes': 'This is a request access test',
            'title': 'Request Access Test Dataset',
            'groups': [{'name': LOCATION_NAME}],
            'owner_org': ORGANIZATION_NAME,
            'maintainer': SYSADMIN_NAME,
            'is_requestdata_type': True,
            'file_types': ['csv'],
            'field_names': ['field1', 'field2']
        }
        pkg_dict = get_action('package_create')(get_sysadmin_context(), package)

        request_access_url = h.url_for('hdx_dataset.request_access', id=pkg_dict.get('name') or pkg_dict.get('id'))

        # GET request without user (anonymous access)
        response = app.get(request_access_url, headers={})
        assert '/sign-in/?info_message_type=hdx-connect' in response.request.url, \
            'Anonymous users should be redirected to the sign-in page with the hdx-connect parameter'
        assert CONST_SIGNIN['hdx-connect'] in response.body, 'Anonymous users should see the HDX Connect info message'

        # GET request with regular user
        response = app.get(request_access_url, headers=auth_headers)
        assert response.status_code == 200
        assert CONST_REQUEST_ACCESS['PAGE_TITLE'] in response.body
        assert CONST_REQUEST_ACCESS['BODY_MAIN_TEXT'] in response.body
        assert 'id="request-access-form"' in response.body, 'The request access form should be visible'

        assert f"'datasetName': '{REQUEST_ACCESS_DATASET_NAME}'," in response.body, ('The analytics info dict should '
                                                                                     'contain dataset name')
        assert "'datasetAvailability': 'metadata only'," in response.body, ('The analytics info dict should contain '
                                                                            'dataset availability')

        # POST request without user (anonymous access)
        response = app.post(request_access_url, data={})
        assert '/sign-in/?info_message_type=hdx-connect' in response.request.url, \
            'Anonymous users should be redirected to the sign-in page with the hdx-connect parameter'
        assert CONST_SIGNIN['hdx-connect'] in response.body,  'Anonymous users should see the HDX Connect info message'

        # POST request with invalid email address & missing fields
        response = app.post(request_access_url, data={'email_address': 'invalid'}, headers=auth_headers)
        assert response.status_code == 200
        assert 'Please provide a valid email address' in response.body, ('There should be an error about invalid email '
                                                                         'format')
        assert 'Missing value' in response.body, 'There should be errors about missing required values'
        assert 'id="request-access-form"' in response.body, 'The request access form should be visible'

        # POST request with valid data
        data_dict = {
            'package_id': pkg_dict.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to access additional data.',
            'organization': 'test_organization',
            'email_address': 'test@test.com',
            'sender_country': 'Sweden',
            'sender_organization_id': 'test_organization',
            'sender_organization_type': 'NGO',
            'sender_intend': 'other',
            'sender_intend_other': 'Testing Purposes',
        }
        response = app.post(request_access_url, data=data_dict, headers=auth_headers)
        assert response.status_code == 200
        assert '<h1 class="heading__title">{0}</h1>'.format(CONST_REQUEST_ACCESS['PAGE_TITLE']) not in response.body
        assert '<h1 class="heading__title">{0}</h1>'.format(
            CONST_REQUEST_ACCESS['PAGE_TITLE_REQUEST_SENT']) in response.body
        assert '<input type="hidden" id="request_sent" value="True">' in response.body, \
            'The hidden input indicates analytics tracking for request submission'

        # POST request with a pending request
        response = app.post(request_access_url, data=data_dict, headers=auth_headers)
        assert response.status_code == 200
        assert 'You already have a pending request. Please wait for the reply.' in response.body, \
            'The same user cannot send another request when there is a pending one'
        assert 'id="request-access-form"' not in response.body, ('The request access form should not be visible for '
                                                                 'pending requests')

    def test_request_access_public_dataset(self, app):
        user_token = factories.APIToken(user=USER_NAME, expires_in=2, unit=60 * 60)['token']
        auth_headers = {'Authorization': user_token}

        package = {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '01/01/1960-12/31/2012',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'Test data',
            'license_id': 'hdx-other',
            'name': PUBLIC_DATASET_NAME,
            'notes': 'This is a public test dataset',
            'title': 'Public Test Dataset',
            'groups': [{'name': LOCATION_NAME}],
            'owner_org': ORGANIZATION_NAME,
            'maintainer': SYSADMIN_NAME,
            'data_update_frequency': '-1',
            'resources': [
                {
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'test.csv'
                }
            ]
        }
        pkg_dict = get_action('package_create')(get_sysadmin_context(), package)

        request_access_url = h.url_for('hdx_dataset.request_access', id=pkg_dict.get('name') or pkg_dict.get('id'))

        # GET request on public dataset
        response = app.get(request_access_url, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when accessing a public dataset')

        # POST request on public dataset
        response = app.post(request_access_url, data={}, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when doing a POST to a public dataset')

    def test_request_access_private_dataset(self, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN_NAME, expires_in=2, unit=60 * 60)['token']
        auth_headers = {'Authorization': sysadmin_token}

        package = {
            'package_creator': 'test function',
            'private': True,
            'dataset_date': '01/01/1960-12/31/2012',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'Test data',
            'license_id': 'hdx-other',
            'name': PRIVATE_DATASET_NAME,
            'notes': 'This is a private test dataset',
            'title': 'Private Test Dataset',
            'groups': [{'name': LOCATION_NAME}],
            'owner_org': ORGANIZATION_NAME,
            'maintainer': SYSADMIN_NAME,
            'data_update_frequency': '-1',
            'resources': [
                {
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'test.csv'
                }
            ]
        }
        pkg_dict = get_action('package_create')(get_sysadmin_context(), package)

        request_access_url = h.url_for('hdx_dataset.request_access', id=pkg_dict.get('name') or pkg_dict.get('id'))

        # GET request on private dataset
        response = app.get(request_access_url, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when accessing a private dataset')

        # POST request on private dataset
        response = app.post(request_access_url, data={}, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when doing a POST to a private dataset')


    def test_request_access_non_existent_dataset(self, app):
        user_token = factories.APIToken(user=USER_NAME, expires_in=2, unit=60 * 60)['token']
        auth_headers = {'Authorization': user_token}

        invalid_url = h.url_for('hdx_dataset.request_access', id='invalid-dataset')

        # GET request on non-existent dataset
        response = app.get(invalid_url, headers=auth_headers)
        assert response.status_code == 404, 'A 404 error should be returned when accessing a non-existent dataset'

        # POST request on non-existent dataset
        response = app.post(invalid_url, data={}, headers=auth_headers)
        assert response.status_code == 404, 'A 404 error should be returned when doing a POST to a non-existent dataset'
