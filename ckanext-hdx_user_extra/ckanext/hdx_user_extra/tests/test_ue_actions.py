'''
Created on February 13, 2020

@author:  Dan


'''
import logging as logging

import pytest
import six

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
import ckanext.hdx_users.helpers.user_extra as ue_helpers

log = logging.getLogger(__name__)


# @pytest.mark.skipif(six.PY3, reason=u'Tests not ready for Python 3')
class TestHDXUserExtra(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        super(TestHDXUserExtra, cls)._create_test_data(create_datasets=True, create_members=True)

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_ue_actions(self):

        context = {'model': model, 'session': model.Session, 'user': 'tester'}
        user = model.User.by_name('tester')
        context['auth_user_obj'] = context['user_obj'] = user
        user.email = 'test@test.com'
        ue_create = self._get_action('user_extra_create')(context, {'user_id': user.id,
                                                                    'extras': ue_helpers.get_initial_extras()})
        assert 9 == len(ue_create)
        ue_show = self._get_action('user_extra_show')(context, {'user_id': user.id})
        assert 9 == len(ue_show)

        ue_create_list = [d.get('value') for i, d in enumerate(ue_create) if
                          d['key'] == 'hdx_onboarding_user_validated']
        ue_show_list = [d.get('value') for i, d in enumerate(ue_show) if d['key'] == 'hdx_onboarding_user_validated']
        assert ue_create_list[0] == ue_show_list[0]

        for ue in ue_show:
            if 'hdx_onboarding_user_validated' == ue.get('key'):
                ue['new_value'] = 'True'
                break

        self._get_action('user_extra_update')(context, {'extras': ue_show, 'user_id': user.id})
        ue_show = self._get_action('user_extra_show')(context, {'user_id': user.id})
        assert 9 == len(ue_show)
        ue_create_list = [d.get('value') for i, d in enumerate(ue_create) if
                          d['key'] == 'hdx_onboarding_user_validated']
        ue_show_list = [d.get('value') for i, d in enumerate(ue_show) if d['key'] == 'hdx_onboarding_user_validated']
        assert ue_create_list[0] != ue_show_list[0]

        assert True
