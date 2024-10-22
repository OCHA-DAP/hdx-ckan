'''
Created on Aug 28, 2014

@author: alexandru-m-g
'''
import pytest
import unicodedata
import logging as logging

import ckan.model as model
import ckan.lib.helpers as h
import ckan.tests.factories as factories

import ckanext.hdx_theme.helpers.helpers as hdx_h

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

log = logging.getLogger(__name__)
pages = [
    # homepage
    {'url_name': 'hdx_splash.index', 'usertype': 'all'},
    {'url_name': 'hdx_splash.index', 'usertype': None},

    # search
    {'url_name': 'hdx_search.search', 'usertype': 'all', 'url_params': {'q': 'test'}},
    {'url_name': 'hdx_search.search', 'usertype': None, 'url_params': {'q': 'test'}},

    # datasets list
    {'url_name': 'hdx_dataset.search', 'usertype': 'all'},
    {'url_name': 'hdx_dataset.search', 'usertype': None},

    # dataset
    {'url_name': 'hdx_dataset.read', 'usertype': 'all', 'url_params': {'id': 'test_dataset_1'}},
    {'url_name': 'hdx_dataset.read', 'usertype': None, 'url_params': {'id': 'test_dataset_1'}},

    # resource
    {'url_name': 'dataset_resource.read', 'usertype': 'sysadmin',
     'url_params': {'id': 'test_private_dataset_1', 'resource_id': '<>'}},

    # showcases list
    {'url_name': 'showcase_blueprint.index', 'usertype': 'all'},
    {'url_name': 'showcase_blueprint.index', 'usertype': None},

    # showcases
    {'url_name': 'showcase_blueprint.read', 'usertype': 'all', 'url_params': {'id': 'test_showcase_1'}},
    {'url_name': 'showcase_blueprint.read', 'usertype': None, 'url_params': {'id': 'test_showcase_1'}},

    # locations/groups list
    {'url_name': 'hdx_group.index', 'usertype': 'all'},
    {'url_name': 'hdx_group.index', 'usertype': None},

    # location/group
    {'url_name': 'hdx_group.read', 'usertype': 'all', 'url_params': {'id': 'roger'}},
    {'url_name': 'hdx_group.read', 'usertype': None, 'url_params': {'id': 'roger'}},

    # organizations list
    {'url_name': 'hdx_org.index', 'usertype': 'all'},
    {'url_name': 'hdx_org.index', 'usertype': None},

    # organization
    {'url_name': 'hdx_org.read', 'usertype': 'all', 'url_params': {'id': 'hdx-test-org'}},
    {'url_name': 'hdx_org.read', 'usertype': None, 'url_params': {'id': 'hdx-test-org'}},

    # login
    {'url_name': 'hdx_signin.login', 'usertype': None},

    # faq
    {'url_name': 'hdx_faqs.read', 'usertype': 'all', 'url_params': {'category': 'faq'}},
    {'url_name': 'hdx_faqs.read', 'usertype': None, 'url_params': {'category': 'faq'}},

    # terms of service
    {'url_name': 'hdx_faqs.read', 'usertype': 'all', 'url_params': {'category': 'terms'}},
    {'url_name': 'hdx_faqs.read', 'usertype': None, 'url_params': {'category': 'terms'}},

    # resources for developers
    {'url_name': 'hdx_faqs.read', 'usertype': 'all', 'url_params': {'category': 'devs'}},
    {'url_name': 'hdx_faqs.read', 'usertype': None, 'url_params': {'category': 'devs'}},

    # data licenses
    {'url_name': 'hdx_faqs.read', 'usertype': 'all', 'url_params': {'category': 'licenses'}},
    {'url_name': 'hdx_faqs.read', 'usertype': None, 'url_params': {'category': 'licenses'}},

    # qa process
    {'url_name': 'hdx_splash.about', 'usertype': 'all', 'url_params': {'page': 'hdx-qa-process'}},
    {'url_name': 'hdx_splash.about', 'usertype': None, 'url_params': {'page': 'hdx-qa-process'}},

    # archive page
    {'url_name': 'hdx_archived_quick_links.show', 'usertype': 'all'},
    {'url_name': 'hdx_archived_quick_links.show', 'usertype': None},

    {'url_name': 'dashboard.organizations', 'usertype': 'all'},
    {'url_name': 'activity.dashboard', 'usertype': 'all'},
    {'url_name': 'hdx_user_dashboard.datasets', 'usertype': 'all'},
    {'url_name': 'dashboard.groups', 'usertype': 'all'},
    {'url_name': 'hdx_user_dashboard.datasets', 'usertype': 'all', 'url_params': {'id': 'tester'}},
    {'url_name': 'hdx_splash.about_hrinfo', 'usertype': 'all'},
]


# @pytest.mark.skipif(six.PY3, reason=u"Needed plugins are not on PY3 yet")
class TestPageLoad(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    tester_token = None
    testsysadmin_token = None
    resource_id = None

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin(
            'hdx_search hdx_org_group hdx_package hdx_users hdx_user_extra hdx_pages hdx_theme')

    @classmethod
    def setup_class(cls):

        import ckanext.hdx_users.model as umodel
        import ckanext.hdx_user_extra.model as ue_model
        import ckanext.hdx_pages.model as p_model

        super(TestPageLoad, cls).setup_class()
        umodel.setup()
        ue_model.create_table()
        p_model.create_table()
        cls.tester_token = factories.APIToken(user='tester', expires_in=2, unit=60 * 60)['token']
        cls.testsysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']

        cls.resource_id = cls._get_action('package_show')(
            {'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'test_private_dataset_1'}
        ).get('resources')[0].get('id')

    @classmethod
    def _create_test_data(cls):
        super(TestPageLoad, cls)._create_test_data(create_datasets=True, create_members=True, create_showcases=True)


    @pytest.mark.parametrize("page", pages)
    def test_page_load(self, page):
        test_client = self.get_backwards_compatible_test_client()
        url_name = page.get('url_name')
        url_params = page.get('url_params')
        if url_params and 'resource_id' in url_params:
            url_params['resource_id'] = self.resource_id

        if not page['usertype']:
            self._try_page_load(test_client, url_name, None, None, url_params)
        else:
            if page['usertype'] == 'user' or page['usertype'] == 'all':
                self._try_page_load(test_client, url_name, 'tester', self.tester_token, url_params)
            if page['usertype'] == 'sysadmin' or page['usertype'] == 'all':
                self._try_page_load(test_client, url_name, 'testsysadmin', self.testsysadmin_token, url_params)

    def _try_page_load(self, test_client, url_name, username, token, url_params=None):
        result = None
        args = []
        kw = {}
        url_for = h.url_for if url_name and '.' in url_name else hdx_h.url_for
        args.append(url_name)

        if url_params:
            kw = url_params
        url = url_for(*args, **kw)
        log.info('Testing url: ' + url)
        if username:
            result = test_client.get(url, headers={'Authorization': unicodedata.normalize(
                'NFKD', token).encode('ascii', 'ignore')})
        else:
            result = test_client.get(url)
        assert ('200' in result.status or '302' in result.status), 'HTTP OK'
        assert 'server error' not in str(result.body).lower()
