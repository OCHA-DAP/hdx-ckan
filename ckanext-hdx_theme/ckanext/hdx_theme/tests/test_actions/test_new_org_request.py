'''
Created on March 21, 2019

@author: dan
'''

import ckan.tests.legacy as tests
import ckan.plugins.toolkit as tk
import ckan.model as model
import logging as logging

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

log = logging.getLogger(__name__)

# (org_name=data_dict.get('name',''), org_description=data_dict.get('description',''),
#                         org_description_data=data_dict.get('description_data',''),
#                         org_work_email=data_dict.get('work_email', ''),
#                         org_url=data_dict.get('org_url',''), org_acronym=data_dict.get('acronym',''),
#                         hdx_org_type=data_dict.get('org_type',''),
#                         person_name=data_dict.get('your_name',''),
#                         person_email=data_dict.get('your_email',''),
#                         ckan_username=ckan_username, ckan_email=ckan_email,
#                         request_time=datetime.datetime.now().isoformat())


postparams = {
    'save': '',
    'name': 'Org êßȘ',
    'acronym': 'SCOACRONYM',
    'org_type': ORGANIZATION_TYPE_LIST[0][1],
    'url': 'http://test.com',
    'description': 'Description ê,ß, and Ș',
    'description_data': 'Description data ê,ß, and Ș',
    'work_email': 'emailwork1@testemail.com',
    'your_email': 'email1@testemail.com',
    'your_name': 'Test êßȘ'
}


class TestNewOrgRequest(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _load_plugins(cls):
        try:
            hdx_test_base.load_plugin('hdx_pages hdx_package hdx_search hdx_org_group hdx_theme')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestNewOrgRequest, cls)._create_test_data(create_datasets=True, create_members=True)

    def test_new_org_request(self):
        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        page_dict = self._get_action('hdx_send_new_org_request')(context, page_elpico)

        # tests.call_action_api(self.app, 'hdx_send_new_org_request',
        #                       title='Org Title', description='Org Description',
        #                       org_url='http://test-org.com/',
        #                       your_name='Some Name', your_email='test@test.com',
        #                       status=404)
