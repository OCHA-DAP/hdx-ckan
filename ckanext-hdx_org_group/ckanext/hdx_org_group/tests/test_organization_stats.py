import pytest
import mock
from ckan.types import Context
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.lib.helpers as h
import ckan.tests.factories as factories
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST


_get_action = tk.get_action
h = tk.h

ADMIN = 'stats_testadmin'
ADMIN_EMAIL = 'stats_testadmin@test.org'

MEMBER = 'stats_testmember'
MEMBER_EMAIL = 'stats_testmember@test.org'

USER = 'stats_testuser'
USER_EMAIL = 'stats_testuser@test.org'

SYSADMIN = 'stats_sysadmin'
SYSADMIN_EMAIL = 'stats_sysadmin@test.org'

ORG_NAME = 'org_name_for_stats'

@pytest.fixture()
def setup_data():
    factories.Sysadmin(name=SYSADMIN, email=SYSADMIN_EMAIL, fullname='Test Sysadmin')
    factories.User(name=USER, email=USER_EMAIL, fullname='Test User')
    factories.User(name=MEMBER, email=MEMBER_EMAIL, fullname='Test Member')
    factories.User(name=ADMIN, email=ADMIN_EMAIL, fullname='Test Admin')
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR JOIN',
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/',
        users=[
            {'name': ADMIN, 'capacity': 'admin'},
            {'name': MEMBER, 'capacity': 'member'},
        ]
    )


def _sysadmin_context():
    return _user_context(SYSADMIN)


def _user_context(user):
    context: Context = {
        'model': model,
        'user': user
    }
    return context


@pytest.mark.usefixtures('clean_db', 'clean_index', 'setup_data')
class TestStatsOrg(object):

    @mock.patch('ckanext.hdx_org_group.helpers.organization_helper._get_mixpanel_data')
    def test_stats_organization(self,hdx_generate_organization_stats, app):
        sysadmin_token = factories.APIToken(user=SYSADMIN, expires_in=2, unit=60 * 60)['token']
        testuser_token = factories.APIToken(user=USER, expires_in=2, unit=60 * 60)['token']
        testadmin_token = factories.APIToken(user=ADMIN, expires_in=2, unit=60 * 60)['token']
        testmember_token = factories.APIToken(user=MEMBER, expires_in=2, unit=60 * 60)['token']
        auth_user = {'Authorization': testuser_token}
        auth_sysadmin = {'Authorization': sysadmin_token}
        auth_admin = {'Authorization': testadmin_token}
        auth_member = {'Authorization': testmember_token}

        org_dict = _get_action('organization_show')(_user_context(USER), {'id': ORG_NAME})
        org_id = org_dict.get('id', ORG_NAME)


        url = h.url_for('hdx_org.stats', id=org_id)
        # no user
        result = app.get(url, headers={})
        assert 'Monthly dataset download and page view statistics' not in result.body
        assert 'If you are an administrator of this organization, you can log in to download monthly statistics going back five years.' in result.body

        url = h.url_for('hdx_org.stats', id=org_id)
        # regular user
        result = app.get(url, headers=auth_user)
        assert 'Monthly dataset download and page view statistics' not in result.body
        assert 'If you are an administrator of this organization, you can log in to download monthly statistics going back five years.' in result.body

        url = h.url_for('hdx_org.stats', id=org_id)
        # org member
        result = app.get(url, headers=auth_member)
        assert 'Monthly dataset download and page view statistics' not in result.body
        assert 'If you are an administrator of this organization, you can log in to download monthly statistics going back five years.' in result.body

        url = h.url_for('hdx_org.stats', id=org_id)
        # org admin
        result = app.get(url, headers=auth_admin)
        assert result.status_code == 200
        assert 'Monthly dataset download and page view statistics' in result.body
        assert 'If you are an administrator of this organization, you can log in to download monthly statistics going back five years.' not in result.body

        # download xls access

        url = h.url_for('hdx_org.download_organization_stats', id=org_id)
        # no user
        result = app.get(url, headers={})
        assert result.status_code == 403

        url = h.url_for('hdx_org.download_organization_stats', id=org_id)
        # regular user
        result = app.get(url, headers=auth_user)
        assert result.status_code == 403

        url = h.url_for('hdx_org.download_organization_stats', id=org_id)
        # org member
        result = app.get(url, headers=auth_member)
        assert result.status_code == 403

        url = h.url_for('hdx_org.download_organization_stats', id=org_id)
        # org admin
        result = app.get(url, headers=auth_admin)
        assert result.status_code == 200
        assert result.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'





