'''
Created on May 16, 2014

@author: alexandru-m-g

'''


import json
import logging

import ckan.model as model
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as tk


import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)

_get_action = tk.get_action

class TestMetadataFields(hdx_test_base.HdxBaseTest):

    def test_cannot_create_dataset_wo_source(self):
        # try:
        #     p.load('hdx_package')
        # except Exception as e:
        #     log.warn('Module already loaded')
        #     log.info(str(e))

        testsysadmin = model.User.by_name('testsysadmin')
        # result = helpers.call_action('package_create', name='test-dataset',
        #         private=False, package_creator='test-creator',
        #         apikey=testsysadmin.apikey, status=409)

        context = {
            'model': model,
            'session': model.Session,
            'user': 'testsysadmin'
        }
        try:
            result = tk.get_action('package_create')(context,{'name': 'test-dataset', 'private':False, 'package_creator':'testsysadmin'})
        except tk.ValidationError as e:
            assert 'dataset_source' in e.error_dict, 'The error needs to be related to the source'
            assert 'Missing value' in e.error_dict['dataset_source'], \
                'The problem needs to be that the source info is missing'
            return

        assert False, 'There should have been a validation error'


    def test_tags_autocomplete(self):
        data_dict = {
            'name': 'Topics',
            'tags': [
                {
                    'name': 'health'
                }
            ]
        }
        _get_action('vocabulary_create')({'ignore_auth': True}, data_dict)

        offset = '/api/2/util/tag/autocomplete?incomplete=a'

        res = self.app.get(offset, )
        assert res.status_code in [200,302]
        r = json.loads(res.body)
        assert len(r['ResultSet']['Result']) > 0

    def _related_create(self, title, description, type, url, image_url):
        usr = _get_action('get_site_user')({'model':model,'ignore_auth': True},{})

        context = dict(model=model, user=usr['name'], session=model.Session)
        data_dict = dict(title=title,description=description,
                         url=url,image_url=image_url,type=type)
        return _get_action("related_create")( context, data_dict )
