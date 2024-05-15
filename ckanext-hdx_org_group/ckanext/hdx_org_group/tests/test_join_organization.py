import mock
import pytest
from ckan.types import Context
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.tests.factories as factories
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST


_get_action = tk.get_action
h = tk.h

USER = 'onboarding_testuser'
USER_EMAIL = 'onboarding_testuser@test.org'

SYSADMIN = 'onboarding_sysadmin'
SYSADMIN_EMAIL = 'onboarding_sysadmin@test.org'

ORG_NAME = 'org_name_for_join'

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

CONST_JOIN_ORG = h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['REQUEST_JOIN_ORGANISATION']
CONST_CONFIRM_ORG= h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['CONFIRM_ORGANISATION_CHOICE']
CONST_REASON_REQUEST_ORG= h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['REASON_REQUEST_ORGANISATION']
CONST_COMPLETED_ORG_REQUEST= h.HDX_CONST('UI_CONSTANTS')['ONBOARDING']['COMPLETED_ORGANISATION_REQUEST']

@pytest.mark.usefixtures("clean_db", "clean_index", "setup_data")
class TestJoinOrg(object):
    #
    @mock.patch('ckanext.ytp.request.logic._mail_new_membership_request')
    def test_join_organization(self,_mail_new_membership_request, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']
        auth_user = {'Authorization': testuser_token}
        auth_sysadmin = {'Authorization': sysadmin_token}

        url = h.url_for('hdx_org_join.org_join')
        # no user
        result = app.get(url, headers={})
        assert result.status_code == 403

        # regular user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 200
        assert CONST_JOIN_ORG['PAGE_TITLE'] in result.body
        assert CONST_JOIN_ORG['BODY_INFO_1ST_PARAGRAPH'] in result.body


        url = h.url_for('hdx_org_join.find_organisation')
        # no user
        result = app.get(url, headers={})
        assert result.status_code == 403
        # registered user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 200
        assert CONST_JOIN_ORG['PAGE_TITLE'] in result.body
        assert CONST_JOIN_ORG['BODY_INFO_1ST_PARAGRAPH'] in result.body

        org_dict = _get_action('organization_show')(_user_context(), {'id': ORG_NAME})
        url = h.url_for('hdx_org_join.confirm_organisation')

        # no user
        result = app.post(url, data={'org_id': org_dict.get('id')}, extra_environ={})
        assert result.status_code == 403

        # get with registered user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 404

        # registered user
        result = app.post(url, data={'org_id': org_dict.get('id')}, extra_environ=auth_user)
        assert result.status_code == 200
        assert org_dict.get('description') in result.body
        assert org_dict.get('title') in result.body
        assert CONST_CONFIRM_ORG['PAGE_TITLE'] in result.body

        url = h.url_for('hdx_org_join.reason_request')
        # no user
        result = app.post(url, data={'org_id': org_dict.get('id')}, extra_environ={})
        assert result.status_code == 403

        # get with registered user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 404

        # registered user
        result = app.post(url, data={'org_id': org_dict.get('id')}, extra_environ=auth_user)
        assert result.status_code == 200
        assert CONST_REASON_REQUEST_ORG['PAGE_TITLE'] in result.body
        assert CONST_REASON_REQUEST_ORG['BODY_MAIN_TEXT'] in result.body


        url = h.url_for('hdx_org_join.completed_request')
        # no user
        result = app.post(url, data={'org_id': org_dict.get('id')}, extra_environ={})
        assert result.status_code == 403

        # get with registered user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 404

        # registered user
        result = app.post(url, data={'org_id': org_dict.get('id'), 'message':'Please let me join'}, extra_environ=auth_user)
        assert result.status_code == 200
        assert CONST_COMPLETED_ORG_REQUEST['PAGE_TITLE'] in result.body
        assert CONST_COMPLETED_ORG_REQUEST['BODY_MAIN_TEXT'] in result.body

        member_list = _get_action('member_request_list')(_sysadmin_context(), {})
        member_dict = member_list[0]
        assert member_dict.get('group_id') == org_dict.get('id')
        assert member_dict.get('group_name') == ORG_NAME
        assert member_dict.get('state') == 'pending'




