import mock
import pytest

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.types import Context
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
h = tk.h

USER = 'onboarding_testuser'
USER_EMAIL = 'onboarding_testuser@test.org'

SYSADMIN = 'onboarding_sysadmin'
SYSADMIN_EMAIL = 'onboarding_sysadmin@test.org'

ORG_NAME = 'org_name_for_request'


@pytest.fixture()
def setup_data():
    factories.Sysadmin(name=SYSADMIN, email=SYSADMIN_EMAIL, fullname='Sysadmin User')
    factories.User(name=USER, email=USER_EMAIL, fullname='Test User')
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR JOIN',
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )


def _sysadmin_context():
    context: Context = {
        'model': model,
        'user': SYSADMIN
    }
    return context


def _user_context():
    context: Context = {
        'model': model,
        'user': USER
    }
    return context


CONST_REQUEST_CREATE_ORG = h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['REQUEST_CREATE_ORGANISATION']
CONST_COMPLETED_CREATE_ORG = h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['COMPLETED_ORGANISATION_CREATE']

NEW_ORGANIZATION_DATA = {
    'name': 'New organization to be created',
    'description': 'Description for new organization',
    'website': 'https://www.organization.com',
    'role': 'Administrator',
    'data_type': 'Humanitarian data',
    'data_already_available': 'yes',
    'data_already_available_link': 'https://data.com',
}


@pytest.mark.usefixtures("clean_db", "clean_index", "setup_data")
class TestRequestOrg(object):
    @mock.patch('ckanext.hdx_org_group.views.organization_request._check_request_referrer_and_access')
    @mock.patch('ckanext.hdx_users.helpers.mailer._mail_recipient_html')
    def test_request_organization(self, _mail_new_membership_request, _check_request_referrer, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']
        auth_user = {'Authorization': testuser_token}
        auth_sysadmin = {'Authorization': sysadmin_token}

        url = h.url_for('hdx_org_request.new')
        # no user
        result = app.get(url, headers={})
        assert result.status_code == 403
        result = app.post(url, data=NEW_ORGANIZATION_DATA, headers={})
        assert result.status_code == 403

        # regular user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 200
        assert CONST_REQUEST_CREATE_ORG['PAGE_TITLE'] in result.body
        assert CONST_REQUEST_CREATE_ORG['BODY_INFO_1ST_PARAGRAPH'] in result.body

        # no user
        result = app.post(url, data=NEW_ORGANIZATION_DATA, extra_environ={})
        assert result.status_code == 403

        # registered user
        _check_request_referrer = True
        result = app.post(url, data=NEW_ORGANIZATION_DATA, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert CONST_COMPLETED_CREATE_ORG['PAGE_TITLE'] in result.body
        assert CONST_COMPLETED_CREATE_ORG['BODY_MAIN_TEXT'] in result.body

        # registered user, wrong organization data
        new_wrong_org_dict = {}
        _check_request_referrer = True
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Missing value') == 5

        new_wrong_org_dict['name'] = 'New organization to be created'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Missing value') == 4

        new_wrong_org_dict['description'] = 'New organization description'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Missing value') == 3

        new_wrong_org_dict['role'] = 'Editor'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Missing value') == 2

        new_wrong_org_dict['data_type'] = 'excel'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Missing value') == 1

        new_wrong_org_dict['data_already_available'] = 'yes'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert CONST_COMPLETED_CREATE_ORG['PAGE_TITLE'] in result.body
        assert CONST_COMPLETED_CREATE_ORG['BODY_MAIN_TEXT'] in result.body

        new_wrong_org_dict['website'] = 'www.no.com'
        new_wrong_org_dict['data_already_available_link'] = 'www.no.com123'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Please provide a valid URL') == 0

        new_wrong_org_dict['website'] = 'http://www.no.com'
        new_wrong_org_dict['data_already_available_link'] = 'http://www.no.com'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Please provide a valid URL') == 0

        new_wrong_org_dict['website'] = 'no.com'
        new_wrong_org_dict['data_already_available_link'] = 'no.com'
        result = app.post(url, data=new_wrong_org_dict, extra_environ=auth_user, follow_redirects=True)
        assert result.status_code == 200
        assert result.body.count('Please provide a valid URL') == 0
