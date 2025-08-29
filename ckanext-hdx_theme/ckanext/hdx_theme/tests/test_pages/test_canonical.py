import pytest
import logging as logging
import six

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_util as hdx_test_util
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import urllib.parse
import html

import ckan.lib.helpers as h
import ckanext.hdx_theme.tests.test_controller.test_responsive_redirect as test_responsive_redirect

log = logging.getLogger(__name__)

no_canonical_pages = [
    ### Dataset pages
    {'url':'dataset_read','id': 'test_dataset_1', 'canonical': False},
    # we need to ignore any params
    {'url':'dataset_read','id': 'test_dataset_1', 'params':{'any_param':'generates_canonical'}, 'canonical': True, 'canonical_url':'dataset_read'},
    # mobile page has canonical
    {'url':'hdx_light_dataset.read','id': 'test_dataset_1', 'mobile': True, 'canonical': True, 'canonical_url':'dataset_read'},

    ### Location pages
    {'url':'hdx_group.read','id': 'roger', 'canonical': False},
    {'url':'hdx_group.read','id': 'roger', 'params':{'any_param':'generates_canonical'}, 'canonical': True, 'canonical_url':'hdx_group.read'},
    {'url':'hdx_light_group.light_read','id': 'roger', 'mobile': True,'canonical': True, 'canonical_url':'hdx_group.read'},

    ### Organization pages
    {'url':'hdx_org.read','id': 'hdx-test-org', 'canonical': False},
    {'url':'hdx_org.read','id': 'hdx-test-org', 'params':{'any_param':'generates_canonical'}, 'canonical': True, 'canonical_url':'hdx_org.read'},
    {'url':'hdx_light_org.light_read','id': 'hdx-test-org', 'params':{'any_param':'generates_canonical'}, 'canonical': True, 'canonical_url':'hdx_org.read'},

    ### Search
    {'url':'/dataset', 'canonical': False},
    # any filter that is allowed (see search/search.html) should not generate canonical
    {'url':'/dataset', 'params':{'license_id':'hdx-other'}, 'canonical': False},
    # any filter by group should generate canonical
    {'url':'/dataset', 'params':{'groups':'roger', 'license_id':'hdx-other'}, 'canonical': True, 'canonical_url':'/dataset',  'canonical_params':{'license_id':'hdx-other'}},
    # any filter by org should generate canonical
    {'url':'/dataset', 'params':{'organization':'hdx-test-org', 'license_id':'hdx-other'}, 'canonical': True, 'canonical_url':'/dataset',  'canonical_params':{'license_id':'hdx-other'}},

    # search queries do generate canonical, for now
    {'url':'/dataset', 'params':{'q':'test', 'sort': 'last_modified desc'}, 'canonical': True, 'canonical_url':'/dataset'},
    {'url':'/dataset', 'params':{'q':'test'}, 'canonical': True, 'canonical_url':'/dataset'},
    # search queries do generate canonical, for now but take into consideration allowed params
    {'url':'/dataset', 'params':{'license_id':'hdx-other', 'q':'test'}, 'canonical': True, 'canonical_url':'/dataset', 'canonical_params':{'license_id':'hdx-other'}},
    # search should add the correct canonical when accepted params are passed, and ignore all the rest (eg. last_modified desc, number of results)
    {'url':'/dataset', 'params':{'license_id':'hdx-other', 'sort': 'last_modified desc', 'ext_page_size': '50'}, 'canonical': True, 'canonical_url':'/dataset',  'canonical_params':{'license_id':'hdx-other'}},
    # search should ignore pagination
    {'url':'/dataset', 'params':{'page': 2}, 'canonical': True, 'canonical_url':'/dataset'},
    {'url':'/dataset', 'params':{'license_id':'hdx-other', 'page': 2}, 'canonical': True, 'canonical_url':'/dataset', 'canonical_params':{'license_id':'hdx-other'}},
    # light search should add canonical
    {'url':'hdx_light_dataset.search', 'mobile': True, 'canonical': True, 'canonical_url':'/dataset'},
    # light search should add canonical just for org
    {'url':'hdx_light_dataset.search', 'params':{'groups':'roger', 'organization':'hdx-test-org'}, 'mobile': True, 'canonical': True, 'canonical_url':'/dataset'},
    # light search should add the correct canonical when accepted params are passed, and ignore all the rest (eg. last_modified desc)
    {'url':'hdx_light_dataset.search', 'params':{'groups':'roger', 'organization':'hdx-test-org', 'license_id':'hdx-other', 'sort': 'last_modified desc'}, 'mobile': True, 'canonical': True, 'canonical_url':'/dataset', 'canonical_params':{'license_id':'hdx-other'}},

]

class TestCanonicalLinks(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @pytest.mark.parametrize(
        "item",
        no_canonical_pages,
        ids=[f"{item.get('url')}-{item.get('id', 'base')}" for item in no_canonical_pages]
    )
    def test_canonical(self, item):
        if item.get('id'):
            url = h.url_for(item['url'], id=item['id'])
        else:
            url = h.url_for(item['url'])

        if item.get('params'):
            url += "?"+urllib.parse.urlencode(item['params'], doseq=True)

        if item.get('mobile') and item['mobile'] == True:
            test_client = self.get_backwards_compatible_test_client()
            result = test_client.get(url, headers={
                'User-Agent': test_responsive_redirect.MOBILE_UA
            })
        else:
            result = self.app.get(url)

        page = result.body

        canonical_str = '<link rel="canonical"'

        if item['canonical'] == False:
            assert canonical_str not in page
        else:
            if item.get('id'):
                canonical_url = h.url_for(item['canonical_url'], id=item['id'])
            else:
                canonical_url = h.url_for(item['canonical_url'])

            if item.get('canonical_params'):
                canonical_url += "?"+ html.escape(urllib.parse.urlencode(item['canonical_params'], doseq=True))

            canonical_str += ' href="'+canonical_url+'"'
            assert canonical_str in page
