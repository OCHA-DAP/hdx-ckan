'''
Created on Sep 9, 2014

@author: alexandru-m-g
'''
import pytest
import json
import unittest.mock as mock
# -*- coding: utf-8 -*-
import logging as logging

import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_user_extra.model as ue_model
import ckanext.hdx_users.model as umodel

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
import ckan.tests.factories as factories

log = logging.getLogger(__name__)
config = tk.config
ValidationError = tk.ValidationError


organization = {
    'name': 'hdx-test-org',
    'title': 'Hdx Test Org',
    'hdx_org_type': ORGANIZATION_TYPE_LIST[0][1],
    'org_acronym': 'HTO',
    'org_url': 'https://test-org.test',
    'description': 'This is a test organization',
    'users': [{'name': 'testsysadmin', 'capacity': 'admin'}, {'name': 'joeadmin', 'capacity': 'admin'}]
}


class TestHDXPackageUpdate(hdx_test_base.HdxBaseTest):
    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_org_group hdx_package hdx_users hdx_user_extra hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    @classmethod
    def setup_class(cls):
        super(TestHDXPackageUpdate, cls).setup_class()
        umodel.setup()
        ue_model.create_table()
        context = {
            'ignore_auth': True,
            'model': model,
            'user': 'testsysadmin'
        }
        cls._get_action('organization_create')(context, organization)

    def test_create_and_upload(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_2',
                   'title': 'Test Activity 2'
                   }

        resource = {
            'package_id': 'test_activity_2',
            'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'hdx_test.csv'
        }

        testsysadmin = model.User.by_name('testsysadmin')

        # Real username is still needed even with ignore_auth otherwise
        # some fields ( like groups ) will not be saved
        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)

        self._get_action('package_create')(context, package)

        self._get_action('resource_create')(context, resource)

        test_url = h.url_for('dataset.read', id=package['name'])
        result = self.app.get(
            test_url, headers={'Authorization': str(testsysadmin.apikey)})
        assert result.status_code == 200
        assert '<a class="heading" title="hdx_test.csv">' in result.body

    def test_resource_create_url_only_reaches_manage_datastore(self):
        """
        Regression test: a URL-only new resource (no uploaded file payload) created via
        resource_create() must still reach _manage_datastore_for_uploads(), since
        package_update()'s FILE_WAS_UPLOADED-based flagging only ever considers resources
        with a truthy 'upload' key (see create.py's `was_real_upload` capture) - it would
        otherwise never be evaluated for DataPusher+ ingestion, even for an eligible
        format/allowlisted dataset (this action explicitly supports creating such
        resources, see test_create_and_upload above).
        """
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_url_only_resource',
                   'title': 'Test Activity Url Only Resource'
                   }

        resource = {
            'package_id': 'test_activity_url_only_resource',
            'url': 'https://example.com/url_only_resource.csv',
            'resource_type': 'url',
            'format': 'CSV',
            'name': 'url_only_resource.csv',
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._get_action('package_create')(context, package)

        with mock.patch(
            'ckanext.hdx_package.actions.create._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            created_resource = self._get_action('resource_create')(context, resource)

        mock_manage_datastore.assert_called_once()
        call_context, call_package = mock_manage_datastore.call_args[0]
        assert call_context.get(FILE_WAS_UPLOADED) == {created_resource['id']}
        assert call_package.get('id') == created_resource['package_id']

    def test_resource_create_real_upload_does_not_double_submit(self):
        """
        Regression test: a genuine file upload must NOT trigger create.py's explicit
        _manage_datastore_for_uploads() call added for the URL-only case above. That
        resource is already fully handled inside package_update()'s own
        FILE_WAS_UPLOADED flagging + _manage_datastore_for_uploads() call, invoked as
        part of the underlying package_revise -> package_update chain for this action.
        Calling it a second time here would submit/evaluate the same resource twice.
        """
        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_real_upload_resource',
                   'title': 'Test Activity Real Upload Resource'
                   }

        resource = {
            'package_id': 'test_activity_real_upload_resource',
            'url': 'https://example.com/uploaded_resource.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'uploaded_resource.csv',
            'upload': 'fake-file-content',  # any truthy value; real uploader is mocked below
        }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._get_action('package_create')(context, package)

        class FakeUpload:
            clear = False
            mimetype = 'text/csv'
            filesize = 10

            def upload(self, resource_id, max_size=None):
                pass

        with mock.patch(
            'ckanext.hdx_package.actions.update.uploader.get_resource_uploader',
            return_value=FakeUpload()
        ), mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ), mock.patch(
            'ckanext.hdx_package.actions.create._manage_datastore_for_uploads'
        ) as mock_manage_datastore_in_create:
            self._get_action('resource_create')(context, resource)

        mock_manage_datastore_in_create.assert_not_called()

    def test_package_update_multiple_new_resources_get_real_ids_flagged(self):
        """
        Regression test for the bug where uploading 2+ brand-new resources in a single
        package_update/package_revise call collapsed into a single 'NEW' sentinel in
        context[FILE_WAS_UPLOADED] (a set), making the individual new resources
        indistinguishable and causing _manage_datastore_for_uploads to silently skip all
        of them (so datapusher+ was never triggered, e.g. for resources added via a
        direct package_revise call with update__resources__extend containing 2+ items).

        After the fix, each new resource must be flagged with its own real resource id.
        """
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_multi_new_resources',
                   'title': 'Test Activity Multi New Resources'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        class FakeUpload:
            clear = False
            mimetype = 'text/csv'
            filesize = 10

            def upload(self, resource_id, max_size=None):
                pass

        # package_update requires the full dataset dict (it isn't a patch), so start from
        # what was just created and only add the two brand-new resources.
        update_dict = dict(created_package)
        update_dict['resources'] = [
            {
                'url': 'https://example.com/new_resource_1.csv',
                'resource_type': 'file.upload',
                'format': 'CSV',
                'name': 'new_resource_1.csv',
                'upload': 'fake-file-1',  # any truthy value; real uploader is mocked below
            },
            {
                'url': 'https://example.com/new_resource_2.csv',
                'resource_type': 'file.upload',
                'format': 'CSV',
                'name': 'new_resource_2.csv',
                'upload': 'fake-file-2',
            },
        ]

        upload_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update.uploader.get_resource_uploader',
            return_value=FakeUpload()
        ), mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ):
            self._get_action('package_update')(upload_context, update_dict)

        uploaded_ids = upload_context.get(FILE_WAS_UPLOADED, set())
        assert 'NEW' not in uploaded_ids
        assert len(uploaded_ids) == 2

        updated_package = self._get_action('package_show')(
            {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': package['name']}
        )
        real_resource_ids = {r['id'] for r in updated_package['resources']}
        assert uploaded_ids == real_resource_ids

    def test_package_update_clear_upload_and_real_upload_flagging(self):
        """
        Regression test for the fix that gates context[FILE_WAS_UPLOADED] flagging on
        `was_real_upload = bool(resource.get('upload'))` instead of on the uploader
        object's truthiness.

        `uploader.get_resource_uploader()` returns a truthy object even when a resource
        is only being *cleared* (via 'clear_upload'), not actually re-uploaded. Before the
        fix, such a resource could be wrongly flagged as a real upload, causing
        _manage_datastore_for_uploads() to submit a cleared resource to DataPusher+, and
        the validators in custom_validator.py (e.g. hdx_reset_on_file_upload) to wrongly
        reset QA/sensitivity metadata on a resource whose file didn't actually change.

        This exercises the real package_update() flagging loop (not a prebuilt context,
        unlike TestManageDatastoreForUploads) for three cases on an *existing* resource:
          1. 'clear_upload' present and truthy, no 'upload' -> must NOT be flagged.
          2. 'clear_upload' present but falsy, no 'upload' -> must NOT be flagged.
          3. a genuine 'upload' value -> must be flagged.
        """
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_clear_upload_flagging',
                   'title': 'Test Activity Clear Upload Flagging',
                   'resources': [
                       {
                           'url': 'https://example.com/existing_resource.csv',
                           'resource_type': 'file.upload',
                           'format': 'CSV',
                           'name': 'existing_resource.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        class FakeUpload:
            clear = False
            mimetype = 'text/csv'
            filesize = 10

            def upload(self, resource_id, max_size=None):
                pass

        def _run_update(resource_overrides):
            update_dict = dict(created_package)
            update_dict['resources'] = [dict(existing_resource, **resource_overrides)]
            update_context = {'ignore_auth': True,
                               'model': model, 'session': model.Session, 'user': 'testsysadmin'}
            with mock.patch(
                'ckanext.hdx_package.actions.update.uploader.get_resource_uploader',
                return_value=FakeUpload()
            ), mock.patch(
                'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
            ):
                self._get_action('package_update')(update_context, update_dict)
            return update_context.get(FILE_WAS_UPLOADED, set())

        # Case 1: clear_upload truthy, no real upload -> must NOT be flagged
        uploaded_ids = _run_update({'clear_upload': True})
        assert existing_resource_id not in uploaded_ids

        # Case 2: clear_upload present but falsy, no real upload -> must NOT be flagged
        uploaded_ids = _run_update({'clear_upload': ''})
        assert existing_resource_id not in uploaded_ids

        # Case 3: genuine upload -> must be flagged
        uploaded_ids = _run_update({'upload': 'fake-file'})
        assert existing_resource_id in uploaded_ids

    def test_package_update_stale_file_was_uploaded_flag_is_cleared(self):
        """
        Regression test for context[FILE_WAS_UPLOADED] leaking stale resource ids across
        multiple package_update() calls that (against CKAN's own convention, but it does
        happen in practice - e.g. via hdx_package_update_metadata(), which forwards its
        caller's context unchanged into package_update()) reuse the SAME context dict.

        Before the fix, context.setdefault(FILE_WAS_UPLOADED, set()) reused whatever set
        was already in the context, so a resource id flagged as "uploaded" by an earlier
        call would still be present during a later, unrelated call (e.g. one that only
        clears the upload) on the same resource - wrongly making validators/datastore
        management treat it as a fresh upload again.

        package_update() must reset context[FILE_WAS_UPLOADED] at the start of every
        invocation, so this test deliberately reuses one context object across two
        sequential calls: first a genuine upload, then a clear_upload-only update.
        """
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_stale_flag_reuse',
                   'title': 'Test Activity Stale Flag Reuse',
                   'resources': [
                       {
                           'url': 'https://example.com/existing_resource.csv',
                           'resource_type': 'file.upload',
                           'format': 'CSV',
                           'name': 'existing_resource.csv',
                       }
                   ]
                   }

        create_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(create_context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        class FakeUpload:
            clear = False
            mimetype = 'text/csv'
            filesize = 10

            def upload(self, resource_id, max_size=None):
                pass

        # A single, shared context reused across both calls below (unlike _run_update()
        # in the previous test, which deliberately uses a fresh context per call).
        shared_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update.uploader.get_resource_uploader',
            return_value=FakeUpload()
        ), mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ):
            # First call: genuine upload -> resource id must be flagged.
            update_dict = dict(created_package)
            update_dict['resources'] = [dict(existing_resource, upload='fake-file')]
            self._get_action('package_update')(shared_context, update_dict)
            assert existing_resource_id in shared_context.get(FILE_WAS_UPLOADED, set())

            # Second call, reusing the SAME context: clear_upload only, no real upload
            # -> the stale flag from the first call must NOT survive into this call.
            update_dict = dict(created_package)
            update_dict['resources'] = [dict(existing_resource, clear_upload=True)]
            self._get_action('package_update')(shared_context, update_dict)
            assert existing_resource_id not in shared_context.get(FILE_WAS_UPLOADED, set())

    def test_hdx_package_delete_redirect(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_3',
                   'title': 'Test Activity 3'
                   }

        testsysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        test_url = h.url_for('dataset.delete', id=package['name'])
        test_client = self.get_backwards_compatible_test_client()
        result = test_client.post(test_url, headers={'Authorization': testsysadmin_token.get('token')})
        assert result.status_code == 302

    def test_hdx_solr_additions(self):
        testsysadmin = model.User.by_name('testsysadmin')
        self._get_action('group_create')(
            {'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'name': 'col', 'title': 'Colombia'}
        )

        context = {'ignore_auth': True,
                                  'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            self._get_action('organization_create')(context, organization)
        except Exception as ex:
            log.error(ex)
        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "col"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_4',
                   'title': 'Test Activity 4',
                   'maintainer': testsysadmin.id,
                   'maintainer_email': None
                   }
        p = self._get_action('package_create')(context, package)
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'nouser'}
        s = self._get_action('package_show')(context, {"id": p.get('id')})
        assert json.loads(s['solr_additions'])['countries'] == ['Colombia']

    def test_hdx_package_update_metadata(self):

        testsysadmin = model.User.by_name('testsysadmin')

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_5',
                   'title': 'Test Activity 5',
                   'maintainer': testsysadmin.id,
                   'maintainer_email': None
                   }



        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        modified_fields = {'id': 'test_activity_5',
                           # 'name': 'test_activity_1_modified',
                           'indicator': '2',
                           # 'title': "Modified Test Activity 1",
                           # 'dataset_source': 'Modified source',
                           'last_metadata_update_date': 'last_metadata_update_date test',
                           'last_data_update_date': 'last_data_update_date test',
                           'dataset_date': '[2014-11-02T00:00:00 TO 2014-11-20T23:59:59]',
                           # 'dataset_source_code': 'dataset_source_code test',
                           'indicator_type': 'indicator_type test',
                           'indicator_type_code': 'indicator_type_code test',
                           # 'dataset_summary': 'dataset_summary test',
                           # 'methodology': 'methodology test',
                           'more_info': 'more_info test',
                           # 'terms_of_use': 'terms_of_use test',
                           'data_update_frequency': '7',
                           'maintainer': testsysadmin.id,
                           'maintainer_email': None
                           }

        self._get_action('hdx_package_update_metadata')(context, modified_fields)

        modified_package = self._get_action('package_show')(
            {'model': model, 'session': model.Session, 'user': 'testsysadmin'},
            {'id': 'test_activity_5'}
        )

        modified_fields.pop('id')

        # Checking that all fields in the modified_package come either
        # from original package or were modified
        for key, value in modified_package.items():
            if key not in modified_fields.keys():
                if key != 'groups' and key in package and key != 'owner_org':
                    assert package[key] == value, 'Problem with key {}: has value {} instead of {}'.format(
                        key, value, package[key])
            else:
                assert value == modified_fields[key], 'Problem with key {}: has value {} instead of {}'.format(
                    key, value, modified_fields[key])

        # Checking that all modifications were applied
        for key, value in modified_fields.items():
            assert value == modified_package[key], 'Problem with key {}: has value {} instead of {}'.format(
                key, modified_package[key], value)

        assert len(modified_package['groups']) == len(
            package['groups']), 'There should be {} item in groups but instead there is {}'.format(
            len(package['groups']), len(modified_package['groups']))

        org_obj = model.Group.by_name('hdx-test-org')
        assert modified_package.get('owner_org') == org_obj.id

    def test_hdx_package_subnational_validation(self):
        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_6',
                   'title': 'Test Activity 6'
                   }

        testsysadmin = model.User.by_name('testsysadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'true')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'True')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', '1')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '1'
        assert modified_package_obj.extras.get('subnational') == '1'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'false')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'False')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', '0')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', 'Dummy Text')
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'subnational', None)
        modified_package = data_dict.get('modified_package')
        modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('subnational') == '0'
        assert modified_package_obj.extras.get('subnational') == '0'

    def test_hdx_package_maintainer_validation(self):

        package = {"package_creator": "test function",
                   "private": False,
                   "dataset_date": "[1960-01-01 TO 2012-12-31]",
                   "caveats": "These are the caveats",
                   "license_other": "TEST OTHER LICENSE",
                   "methodology": "This is a test methodology",
                   "dataset_source": "World Bank",
                   "license_id": "hdx-other",
                   "notes": "This is a test activity",
                   "groups": [{"name": "roger"}],
                   "owner_org": "hdx-test-org",
                   'name': 'test_activity_7',
                   'title': 'Test Activity 7',
                   'maintainer': 'testsysadmin'
                   }

        testsysadmin = model.User.by_name('testsysadmin')
        joeadmin = model.User.by_name('joeadmin')

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        # self._get_action('organization_create')(context, organization)
        self._get_action('package_create')(context, package)
        # This is a copy of the hack done in dataset_controller
        self._get_action('package_update')(context, package)

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'testsysadmin')
        modified_package = data_dict.get('modified_package')
        # modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('maintainer') == testsysadmin.id

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'joeadmin')
        modified_package = data_dict.get('modified_package')
        # modified_package_obj = data_dict.get('modified_package_obj')
        assert modified_package.get('maintainer') == joeadmin.id

        try:
            data_dict = self._modify_field(context, testsysadmin, package['name'], 'maintainer', 'joeadmin no user')
            assert False, 'There should have been a validation error'
        except ValidationError as e:
            pass

        modified_package = data_dict.get('modified_package')
        assert modified_package.get('maintainer') == joeadmin.id

    def test_hdx_package_tags_validation(self):
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "World Bank",
            "license_id": "hdx-other",
            "notes": "This is a test activity",
            "groups": [{"name": "roger"}],
            "owner_org": "hdx-test-org",
            'name': 'test_activity_8',
            'title': 'Test Activity 8',
            'maintainer': 'testsysadmin'
        }

        testsysadmin = model.User.by_name('testsysadmin')
        joeadmin = model.User.by_name('joeadmin')

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        context_user = {'model': model, 'session': model.Session, 'user': 'joeadmin', 'auth_user_obj': joeadmin}

        pkg_dict = self._get_action('package_create')(context, package)

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'tags', [{'name': 'children'}])
        modified_package = data_dict.get('modified_package')

        assert len(pkg_dict.get('tags')) == 0
        assert len(modified_package.get('tags')) == 1
        assert 'children' in [tag['name'] for tag in modified_package.get('tags')]

        crisis_tag_name = 'crisis-opt-israel-hostilities'
        data_dict = self._modify_field(context, testsysadmin, package['name'], 'tags',
                                       [{'name': crisis_tag_name}, {'name': 'children'}])
        modified_package = data_dict.get('modified_package')

        assert len(modified_package.get('tags')) == 2
        assert crisis_tag_name in [tag['name'] for tag in modified_package.get('tags')]
        assert 'children' in [tag['name'] for tag in modified_package.get('tags')]

        try:
            self._modify_field(context, testsysadmin, package['name'], 'tags',
                               [{'name': 'invalid_tag1'}, {'name': 'invalid_tag2'}])
        except ValidationError as e:
            assert 'tags' in e.error_dict, 'package_update should fail when using invalid tags'
            assert len(e.error_dict.get('tags')) == 2, 'There should be two invalid tags'
            assert "Tag name 'invalid_tag1' is not in the approved list of tags" in e.error_dict.get('tags')[0]

        try:
            self._modify_field(context_user, joeadmin, package['name'], 'tags', [{'name': crisis_tag_name}])
        except ValidationError as e:
            assert 'tags' in e.error_dict, 'Only sysadmins are allowed to add tags starting with "crisis-"'
            assert "Tag name '{}' can only be added by sysadmins".format(crisis_tag_name) in e.error_dict.get('tags')[
                0], 'Only sysadmins are allowed to add tags starting with "crisis-"'

        data_dict = self._modify_field(context_user, joeadmin, package['name'], 'tags',
                                       [{'name': crisis_tag_name}, {'name': 'disease'}])
        modified_package = data_dict.get('modified_package')

        assert len(modified_package.get('tags')) == 2
        assert crisis_tag_name in [tag['name'] for tag in modified_package.get(
            'tags')], 'Crisis tags should be kept if specified by a user, as they were already added by a sysadmin'
        assert 'disease' in [tag['name'] for tag in modified_package.get('tags')]

        data_dict = self._modify_field(context_user, joeadmin, package['name'], 'tags', [{'name': 'boys'}])
        modified_package = data_dict.get('modified_package')

        assert len(modified_package.get('tags')) == 2
        assert 'boys' in [tag['name'] for tag in modified_package.get('tags')], \
            'Crisis tags should be kept even if not specified by a user, as they were already added by a sysadmin'

        data_dict = self._modify_field(context, testsysadmin, package['name'], 'tags',
                                       [{'name': 'boys'}, {'name': 'disease'}])
        modified_package = data_dict.get('modified_package')

        assert len(modified_package.get('tags')) == 2
        assert 'boys' in [tag['name'] for tag in modified_package.get('tags')], \
            'Crisis tags should be removed if not specified by a sysadmin'


    def _modify_field(self, context, user, package_id, key, value):
        modified_fields = {'id': package_id,
                           key: value,
                           }
        self._get_action('package_patch')(context, modified_fields)
        modified_package = self._get_action('package_show')(
            {'model': model, 'session': model.Session, 'user': user.name},
            {'id': package_id}
        )
        modified_package_obj = model.Package.by_name(package_id)
        return {
            "modified_package": modified_package,
            "modified_package_obj": modified_package_obj
        }


class TestManageDatastoreForUploads:
    """
    Pure unit tests for _manage_datastore_for_uploads.
    No database or Solr required — all external calls are mocked.
    """

    RESOURCE_ID = 'res-001'
    PACKAGE_ID = 'pkg-001'

    def _make_context(self, resource_ids=None):
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED
        ids = resource_ids if resource_ids is not None else {self.RESOURCE_ID}
        return {FILE_WAS_UPLOADED: ids}

    def _make_package_dict(self, resource_format='CSV'):
        return {
            'id': self.PACKAGE_ID,
            'resources': [
                {
                    'id': self.RESOURCE_ID,
                    'format': resource_format,
                }
            ],
        }

    def _run(self, context, package_dict, get_action_mock, configured_formats=None):
        import ckan.plugins as ckan_plugins
        from ckanext.hdx_package.actions.update import _manage_datastore_for_uploads

        fake_dp_plugin = mock.MagicMock()
        fake_dp_plugin.name = 'datapusher_plus'

        with mock.patch(
            'ckanext.hdx_package.actions.update._get_action',
            side_effect=get_action_mock
        ), mock.patch(
            'ckanext.hdx_package.actions.update.tk'
        ) as mock_tk, mock.patch.object(
            ckan_plugins, 'PluginImplementations', return_value=[fake_dp_plugin]
        ):
            formats = configured_formats if configured_formats is not None else ['csv', 'xls', 'xlsx', 'tsv']
            mock_tk.config.get.side_effect = lambda key, default=None: (
                formats if 'formats' in key else default
            )
            _manage_datastore_for_uploads(context, package_dict)

        return fake_dp_plugin

    def _make_get_action(self, hdx_allowed=True, datastore_exists=True):
        import ckan.plugins.toolkit as real_tk
        datastore_delete_mock = mock.MagicMock()
        datastore_search_mock = mock.MagicMock()
        if not datastore_exists:
            datastore_search_mock.side_effect = real_tk.ObjectNotFound()

        def side_effect(action_name):
            if action_name == 'hdx_is_package_allowed_for_datastore':
                return lambda ctx, data: hdx_allowed
            if action_name == 'datastore_delete':
                return datastore_delete_mock
            if action_name == 'datastore_search':
                return datastore_search_mock
            return mock.MagicMock()

        return side_effect, datastore_delete_mock

    def test_submit_when_eligible(self):
        """CSV + allowlist=True → submit called, datastore_delete NOT called."""
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=True)
        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='CSV'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_called_once()
        datastore_delete_mock.assert_not_called()

    def test_delete_when_format_not_supported(self):
        """PDF + datastore table exists + allowlist=True → datastore_delete called, submit NOT called."""
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=True, datastore_exists=True)
        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='PDF'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_not_called()
        datastore_delete_mock.assert_called_once_with(
            {'ignore_auth': True},
            {'resource_id': self.RESOURCE_ID, 'force': True},
        )

    def test_delete_when_not_hdx_allowed(self):
        """CSV + datastore table exists + allowlist=False → datastore_delete called, submit NOT called."""
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=False, datastore_exists=True)
        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='CSV'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_not_called()
        datastore_delete_mock.assert_called_once_with(
            {'ignore_auth': True},
            {'resource_id': self.RESOURCE_ID, 'force': True},
        )

    def test_no_action_when_ineligible_and_no_datastore_table(self):
        """PDF + no datastore table + allowlist=True → neither submit nor delete called."""
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=True, datastore_exists=False)
        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='PDF'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_not_called()
        datastore_delete_mock.assert_not_called()

    def test_no_action_for_unmatched_id(self):
        """
        FILE_WAS_UPLOADED containing an id with no matching resource in package_dict
        (e.g. a stale/unknown id) → neither submit nor delete called.

        Note: package_update() no longer produces a literal 'NEW' sentinel (see
        test_package_update_multiple_new_resources_get_real_ids_flagged in
        test_package_update.py's TestHDXPackageUpdate for the regression test covering
        that fix) — this test just verifies _manage_datastore_for_uploads()'s generic,
        defensive handling of any id that doesn't resolve to a resource.
        """
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=True)
        fake_dp_plugin = self._run(
            self._make_context(resource_ids={'some-unknown-id'}),
            self._make_package_dict(resource_format='CSV'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_not_called()
        datastore_delete_mock.assert_not_called()

    def test_skip_on_allowlist_exception(self):
        """Exception from allowlist lookup → returns early; neither submit nor delete called."""
        datastore_delete_mock = mock.MagicMock()

        def get_action_side_effect(action_name):
            if action_name == 'hdx_is_package_allowed_for_datastore':
                def raise_exc(ctx, data):
                    raise Exception('Spreadsheet fetch failed')
                return raise_exc
            if action_name == 'datastore_delete':
                return datastore_delete_mock
            return mock.MagicMock()

        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='CSV'),
            get_action_side_effect,
        )
        fake_dp_plugin._submit_to_datapusher.assert_not_called()
        datastore_delete_mock.assert_not_called()

    def test_submit_when_formats_config_is_string(self):
        """CSV + string config value → submit called, datastore_delete NOT called."""
        get_action_side_effect, datastore_delete_mock = self._make_get_action(hdx_allowed=True)
        fake_dp_plugin = self._run(
            self._make_context(),
            self._make_package_dict(resource_format='CSV'),
            get_action_side_effect,
            configured_formats='csv xls xlsx tsv',
        )
        fake_dp_plugin._submit_to_datapusher.assert_called_once()
        datastore_delete_mock.assert_not_called()
