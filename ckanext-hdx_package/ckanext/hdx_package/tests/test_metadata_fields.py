'''
Created on May 16, 2014

@author: alexandru-m-g

'''


import json
import webtest
import logging

import ckan.plugins as p
import ckan.lib.create_test_data as ctd
import ckan.lib.search as search
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
import ckan.tests.legacy as legacy_tests

from ckan.config.middleware import make_app
from pylons import config

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_package.helpers.caching as caching

log = logging.getLogger(__name__)


class TestMetadataFields(hdx_test_base.HdxBaseTest):

    def test_cannot_create_dataset_wo_source(self):
        try:
            p.load('hdx_package')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

        testsysadmin = model.User.by_name('testsysadmin')
        result = legacy_tests.call_action_api(self.app, 'package_create', name='test-dataset',
                private=False, package_creator='test-creator',
                apikey=testsysadmin.apikey, status=409)

#         result = tk.get_action('package_create')({'user':'testsysadmin'},{'name': 'test-dataset', 'private':False})

        assert 'dataset_source' in result, 'The error needs to be related to the source'
        assert 'Missing value' in result['dataset_source'], 'The problem needs to be that the source info is missing'


    # def test_private_is_private(self):
    #     try:
    #         p.load('hdx_package')
    #     except Exception as e:
    #         log.warn('Module already loaded')
    #         log.info(str(e))

    #     tester = model.User.by_name('tester')
    #     tests.call_action_api(self.app, 'organization_create',
    #                                     name='test_org_2',
    #                                     apikey=tester.apikey)

    #     tests.call_action_api(self.app, 'package_create', name='test-dataset-private',
    #             private=True, owner_org='test_org_2',package_creator='test-creator', dataset_source='test',
    #             resources=[{'url':'text_upload_file.txt'}], apikey=tester.apikey, status=409)
    #     ds = tests.call_action_api(self.app, 'package_show', id='test-dataset-private', apikey=tester.apikey, status=409)
    #     r =  requests.get(ds['resources'][0]['url'])
    #     assert r.text == 'Hello World'



    def test_tags_autocomplete(self):
        data_dict = {
            'name': 'Topics',
            'tags': [
                {
                    'name': 'health'
                }
            ]
        }
        logic.get_action('vocabulary_create')({'ignore_auth': True}, data_dict)

        offset = '/api/2/util/tag/autocomplete?incomplete=a'

        res = self.app.get(offset, )
        assert res.status_code in [200,302]
        r = json.loads(res.body)
        assert len(r['ResultSet']['Result']) > 0

    def _related_create(self, title, description, type, url, image_url):
        usr = logic.get_action('get_site_user')({'model':model,'ignore_auth': True},{})

        context = dict(model=model, user=usr['name'], session=model.Session)
        data_dict = dict(title=title,description=description,
                         url=url,image_url=image_url,type=type)
        return logic.get_action("related_create")( context, data_dict )
