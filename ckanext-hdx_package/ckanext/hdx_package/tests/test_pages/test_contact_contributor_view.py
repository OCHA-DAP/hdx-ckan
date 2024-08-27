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
PUBLIC_DATASET_NAME = 'public_test_dataset'
REQUEST_DATA_DATASET_NAME = 'contact_contributor_test_dataset'
CONST_CONTACT_CONTRIBUTOR = h.HDX_CONST('UI_CONSTANTS')['CONTACT_CONTRIBUTOR']
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
class TestContactContributorView(object):
    @mock.patch('ckanext.hdx_package.actions.get.hdx_mailer.mail_recipient')
    def test_contact_contributor(self, mock_mail_recipient, app):
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

        contact_contributor_url = h.url_for('hdx_dataset.contact_contributor', id=pkg_dict.get('name') or pkg_dict.get('id'))

        # GET request without user (anonymous access)
        response = app.get(contact_contributor_url, headers={})
        assert '/sign-in/?info_message_type=contact-contributor' in response.request.url, \
            'Anonymous users should be redirected to the sign-in page with the contact-contributor parameter'
        assert CONST_SIGNIN['contact-contributor'] in response.body, 'Anonymous users should see the contact contributor info message'

        # GET request with regular user
        response = app.get(contact_contributor_url, headers=auth_headers)
        assert response.status_code == 200
        assert CONST_CONTACT_CONTRIBUTOR['PAGE_TITLE'] in response.body
        assert CONST_CONTACT_CONTRIBUTOR['BODY_MAIN_TEXT'] in response.body
        assert 'id="contact-contributor-form"' in response.body, 'The contact contributor form should be visible'

        assert f"'datasetName': '{PUBLIC_DATASET_NAME}'," in response.body, \
            'The analytics info dict should contain dataset name'

        # POST request without user (anonymous access)
        response = app.post(contact_contributor_url, data={})
        assert '/sign-in/?info_message_type=contact-contributor' in response.request.url, \
            'Anonymous users should be redirected to the sign-in page with the contact-contributor parameter'
        assert CONST_SIGNIN['contact-contributor'] in response.body,  'Anonymous users should see the contact contributor info message'

        # POST request with invalid email address & missing fields
        response = app.post(contact_contributor_url, data={'email': 'invalid'}, headers=auth_headers)
        assert response.status_code == 200
        assert 'Email invalid is not a valid format' in response.body, \
            'There should be an error about invalid email format'
        assert 'Missing value' in response.body, 'There should be errors about missing required values'
        assert 'id="contact-contributor-form"' in response.body, 'The contact contributor form should be visible'

        # POST request with valid data
        data_dict = {
            'topic': 'suggested edits',
            'fullname': 'John Doe',
            'email': 'hdx.feedback@gmail.com',
            'msg': 'my message',
            'pkg_id': pkg_dict.get('id'),
            'pkg_owner_org': pkg_dict.get('owner_org'),
            'pkg_title': pkg_dict.get('title'),
        }
        response = app.post(contact_contributor_url, data=data_dict, headers=auth_headers)
        assert response.status_code == 200
        assert '<h1 class="heading__title">{0}</h1>'.format(CONST_CONTACT_CONTRIBUTOR['PAGE_TITLE']) not in response.body
        assert '<h1 class="heading__title">{0}</h1>'.format(
            CONST_CONTACT_CONTRIBUTOR['PAGE_TITLE_MESSAGE_SENT']) in response.body
        assert '<input type="hidden" id="message_sent" value="True">' in response.body, \
            'The hidden input indicates analytics tracking for request submission'
        assert ('<input type="hidden" id="message_subject" value="{0}">'.format(data_dict.get('topic')) in
                response.body), 'The hidden input indicates analytics tracking message subject for request submission'

    def test_contact_contributor_request_data_dataset(self, app):
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
            'name': REQUEST_DATA_DATASET_NAME,
            'notes': 'This is a contact contributor test',
            'title': 'Request Access Test Dataset',
            'groups': [{'name': LOCATION_NAME}],
            'owner_org': ORGANIZATION_NAME,
            'maintainer': SYSADMIN_NAME,
            'is_requestdata_type': True,
            'file_types': ['csv'],
            'field_names': ['field1', 'field2']
        }
        pkg_dict = get_action('package_create')(get_sysadmin_context(), package)

        contact_contributor_url = h.url_for('hdx_dataset.contact_contributor', id=pkg_dict.get('name') or pkg_dict.get('id'))

        # GET request on HDX Connect dataset
        response = app.get(contact_contributor_url, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when accessing a HDX Connect dataset')

        # POST request on HDX Connect dataset
        response = app.post(contact_contributor_url, data={}, headers=auth_headers)
        assert response.status_code == 404, ('A 404 error should be returned when doing a POST to a HDX Connect dataset')


    def test_contact_contributor_non_existent_dataset(self, app):
        user_token = factories.APIToken(user=USER_NAME, expires_in=2, unit=60 * 60)['token']
        auth_headers = {'Authorization': user_token}

        invalid_url = h.url_for('hdx_dataset.contact_contributor', id='invalid-dataset')

        # GET request on non-existent dataset
        response = app.get(invalid_url, headers=auth_headers)
        assert response.status_code == 404, 'A 404 error should be returned when accessing a non-existent dataset'

        # POST request on non-existent dataset
        response = app.post(invalid_url, data={}, headers=auth_headers)
        assert response.status_code == 404, 'A 404 error should be returned when doing a POST to a non-existent dataset'
