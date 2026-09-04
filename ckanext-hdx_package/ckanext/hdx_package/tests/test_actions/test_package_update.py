'''
Created on Sep 9, 2014

@author: alexandru-m-g
'''
import pytest
import datetime
import json
import uuid
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
        resource_create() must still reach _manage_datastore_for_uploads(), since it's
        a brand-new resource - package_update()'s flagging loop flags every brand-new
        resource (real upload or not) once its real id is known (post-flush), not just
        ones with a truthy 'upload' key. This is exercised here through resource_create()'s
        underlying package_revise -> package_update call chain (this action explicitly
        supports creating such resources, see test_create_and_upload above).
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
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            created_resource = self._get_action('resource_create')(context, resource)

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert created_resource['id'] in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_resource['package_id']

    def test_package_revise_direct_url_only_new_resource_reaches_manage_datastore(self):
        """
        Regression test: a URL-only new resource added via a DIRECT package_revise()
        call (update__resources__extend), with NO resource_create() involved at all,
        must still reach _manage_datastore_for_uploads(). package_revise's own docstring
        explicitly advertises update__resources__extend as a supported way to add a new
        resource, so this call pattern must be covered too, not just resource_create().
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
                   'name': 'test_activity_direct_revise_url_only',
                   'title': 'Test Activity Direct Revise Url Only'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        revise_dict = {
            'match': {'id': created_package['id']},
            'update__resources__extend': [{
                'url': 'https://example.com/direct_revise_url_only.csv',
                'resource_type': 'url',
                'format': 'CSV',
                'name': 'direct_revise_url_only.csv',
            }]
        }

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            revise_response = self._get_action('package_revise')(context, revise_dict)

        new_resource_id = revise_response['package']['resources'][-1]['id']

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert new_resource_id in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_package['id']

    def test_package_revise_new_resource_with_caller_supplied_id_reaches_manage_datastore(self):
        """
        Regression test: a brand-new resource added via a DIRECT package_revise() call
        (update__resources__extend) where the CALLER supplies its own pre-generated,
        non-conflicting UUID as the resource 'id' (e.g. an ignore_auth/sysadmin script,
        harvester, or migration job that wants a deterministic id) must still be treated
        as NEW and reach _manage_datastore_for_uploads().

        CKAN core's resource_dict_save() (ckan/lib/dictization/model_save.py) determines
        newness by whether a DB row already exists for the given id
        (`session.query(model.Resource).get(id)`), NOT by whether the incoming dict has an
        'id' key at all. Before the fix, package_update() used
        `not bool(resource.get('id'))` to decide "newness", which wrongly classified this
        caller-supplied-id-but-not-yet-existing resource as "existing" - so it was never
        flagged in context[FILE_WAS_UPLOADED], and DataPusher+/datastore management was
        silently skipped for it.
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
                   'name': 'test_activity_caller_supplied_id',
                   'title': 'Test Activity Caller Supplied Id'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        caller_generated_id = str(uuid.uuid4())  # does not exist in the DB yet

        revise_dict = {
            'match': {'id': created_package['id']},
            'update__resources__extend': [{
                'id': caller_generated_id,
                'url': 'https://example.com/caller_supplied_id.csv',
                'resource_type': 'url',
                'format': 'CSV',
                'name': 'caller_supplied_id.csv',
            }]
        }

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            revise_response = self._get_action('package_revise')(context, revise_dict)

        new_resource_id = revise_response['package']['resources'][-1]['id']
        assert new_resource_id == caller_generated_id

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert new_resource_id in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_package['id']

    def test_package_update_new_resource_with_caller_supplied_id_not_flagged_pre_validation(self):
        """
        Regression test: a brand-new resource with a caller-supplied id (not yet in the
        DB) AND a real file upload must NOT be flagged into context[FILE_WAS_UPLOADED]
        during STAGE 1 (pre-validation) - only truly EXISTING resources should be
        flagged there (see the two-stage flagging design documented above the
        pre-validation loop in package_update()).

        hdx_reset_on_file_upload (used for pii_is_sensitive, in_quarantine,
        qa_hapi_report, sensitive, sdd_report) unconditionally pops those fields for any
        resource id present in FILE_WAS_UPLOADED *during validation*. A brand-new
        resource has no stale previous value to reset, so flagging it at stage 1 would
        wrongly discard values the caller explicitly set on creation. It must still be
        correctly flagged at STAGE 2 (post-flush, via `was_new`), so DataPusher+
        submission is unaffected - this test only asserts on the STAGE 1 (pre-validation)
        snapshot.
        """
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED
        import ckanext.hdx_package.actions.update as update_module

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
                   'name': 'test_activity_new_resource_caller_id_pre_validation',
                   'title': 'Test Activity New Resource Caller Id Pre Validation'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        caller_generated_id = str(uuid.uuid4())  # does not exist in the DB yet

        class FakeUpload:
            clear = False
            mimetype = 'text/csv'
            filesize = 10

            def upload(self, resource_id, max_size=None):
                pass

        update_dict = dict(created_package)
        update_dict['resources'] = [{
            'id': caller_generated_id,
            'url': 'https://example.com/new_with_caller_id.csv',
            'resource_type': 'file.upload',
            'format': 'CSV',
            'name': 'new_with_caller_id.csv',
            'upload': 'fake-file',
        }]

        captured_stage1_flags = {}
        real_plugin_validate = update_module.lib_plugins.plugin_validate

        def spy_plugin_validate(package_plugin, ctx, data, schema, action):
            # lib_plugins.plugin_validate() is also called internally for OTHER actions
            # (e.g. package_show, invoked later for indexing/reading back the result) -
            # only capture the snapshot for the package_update validation call itself,
            # otherwise a later unrelated call would overwrite our stage-1 snapshot.
            if action == 'package_update' and 'ids' not in captured_stage1_flags:
                captured_stage1_flags['ids'] = set(ctx.get(FILE_WAS_UPLOADED, set()))
            return real_plugin_validate(package_plugin, ctx, data, schema, action)

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update.uploader.get_resource_uploader',
            return_value=FakeUpload()
        ), mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ), mock.patch(
            'ckanext.hdx_package.actions.update.lib_plugins.plugin_validate',
            side_effect=spy_plugin_validate
        ):
            self._get_action('package_update')(update_context, update_dict)

        # STAGE 1 (captured DURING validation, before the resource has a real DB row):
        # the caller-supplied new id must NOT be flagged yet.
        assert caller_generated_id not in captured_stage1_flags['ids']

        # STAGE 2 (post-flush, checked AFTER the call returns): it must still end up
        # flagged so DataPusher+ submission isn't affected by this fix.
        assert caller_generated_id in update_context.get(FILE_WAS_UPLOADED, set())

    @pytest.mark.xfail(
        reason=(
            "Documents an inherent CKAN-core gap (ckan/model/modification.py: "
            "DomainObjectModificationExtension.before_commit dispatches "
            "IResourceUrlChange.notify() with NO exception guard) that cannot be fixed "
            "from an extension without patching core. Our real mitigation is that "
            "DatapusherPlusPlugin.notify() (src/datapusher-plus) is now an intentional "
            "no-op, and package_update() itself now covers 'existing resource url "
            "changed' via existing_resource_urls (see "
            "test_package_update_existing_resource_url_change_reaches_manage_datastore) "
            "- so in practice nothing HDX-controlled raises from this hook anymore. This "
            "test uses a synthetic third-party-style plugin to prove the core dispatch "
            "itself still has no safety net, in case any OTHER plugin implements this "
            "interface unsafely."
        ),
        strict=True,
    )
    def test_resource_url_change_commit_hook_exception_does_not_propagate(self):
        """
        Regression test / KNOWN FAILURE: CKAN core's commit-time IResourceUrlChange hook
        (ckan/model/modification.py: DomainObjectModificationExtension.before_commit ->
        notify_observers()) has NO exception guard around it, unlike the fail-open
        guarantee package_update() otherwise builds for DataPusher+/datastore management
        (see the try/except around _manage_datastore_for_uploads() a few lines after
        model.repo.commit() in package_update()).

        Whenever an EXISTING resource's 'url' (or 'last_modified') changes,
        resource_dict_save() sets obj.url_changed = True, and that same core before_commit
        hook then calls IResourceUrlChange.notify() for every plugin implementing that
        interface - synchronously, DURING model.repo.commit() (i.e. BEFORE our own
        post-commit try/except is even reached), and with no try/except of its own
        (contrast with the IDomainObjectModification dispatch a few lines below it in the
        same file, which IS wrapped in try/except).

        DatapusherPlusPlugin.notify() (src/datapusher-plus/ckanext/datapusher_plus/
        plugin.py) has since been made an intentional no-op specifically because of this
        gap - see its docstring/comment. This test doesn't require datapusher_plus to be
        loaded at all - it simulates the exact same unguarded core dispatch with a
        minimal synthetic fake plugin that raises, to prove the CORE mechanism itself
        still provides no safety net for whatever plugin implements this interface. This
        is expected to keep failing (xfail, strict) until CKAN core adds a guard here -
        which is out of scope for our extensions.
        """
        import ckan.plugins as ckan_plugins

        class RaisingUrlChangePlugin:
            def notify(self, resource):
                raise Exception('simulated DataPusher+ failure from IResourceUrlChange.notify()')

        real_plugin_implementations = ckan_plugins.PluginImplementations

        def plugin_implementations_side_effect(interface):
            if interface is ckan_plugins.IResourceUrlChange:
                return [RaisingUrlChangePlugin()]
            return real_plugin_implementations(interface)

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
                   'name': 'test_activity_url_change_commit_hook',
                   'title': 'Test Activity Url Change Commit Hook',
                   'resources': [
                       {
                           'url': 'https://example.com/original.csv',
                           'resource_type': 'url',
                           'format': 'CSV',
                           'name': 'original.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]

        update_dict = dict(created_package)
        # Changing the url is what sets obj.url_changed = True inside
        # resource_dict_save(), which is what makes CKAN core dispatch
        # IResourceUrlChange.notify() during model.repo.commit() below.
        update_dict['resources'] = [dict(existing_resource, url='https://example.com/changed.csv')]

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckan.plugins.PluginImplementations',
            side_effect=plugin_implementations_side_effect
        ), mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ):
            # This must NOT raise - a failure from this commit-time hook must not abort
            # an otherwise-successful package_update() call, consistent with every other
            # fail-open guarantee already covered elsewhere in this test file.
            result = self._get_action('package_update')(update_context, update_dict)

        assert result['resources'][0]['url'] == 'https://example.com/changed.csv'

    def test_package_update_existing_resource_url_change_reaches_manage_datastore(self):
        """
        Regression test for existing_resource_urls: an EXISTING resource whose 'url'
        changes with NO 'upload'/'clear_upload' key at all (e.g. a link-type resource
        whose url is edited directly through the form/API) must still be flagged into
        context[FILE_WAS_UPLOADED] and reach _manage_datastore_for_uploads().

        This scenario used to be covered exclusively by CKAN core's commit-time
        IResourceUrlChange hook (DatapusherPlusPlugin.notify(), dispatched from
        DomainObjectModificationExtension.before_commit() DURING model.repo.commit(),
        with no exception guard - see
        test_resource_url_change_commit_hook_exception_does_not_propagate). That hook is
        now an intentional no-op, so package_update() itself must cover this case via its
        own existing_resource_urls tracking, flowing through the already fail-open,
        POST-commit _manage_datastore_for_uploads() call instead.
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
                   'name': 'test_activity_existing_resource_url_change',
                   'title': 'Test Activity Existing Resource Url Change',
                   'resources': [
                       {
                           'url': 'https://example.com/original_url_change.csv',
                           'resource_type': 'url',
                           'format': 'CSV',
                           'name': 'original_url_change.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        update_dict = dict(created_package)
        # No 'upload'/'clear_upload' key at all here - just a plain url edit, which is
        # exactly the case existing_resource_urls exists to cover.
        update_dict['resources'] = [dict(existing_resource, url='https://example.com/changed_url_change.csv')]

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert existing_resource_id in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_package['id']

    def test_package_update_upload_resource_unchanged_url_not_falsely_flagged(self):
        """
        Regression test for the url_type == 'upload' branch of the url-change detection
        (existing_resource_urls comparison): a "load, then save back unchanged" round trip
        on an existing upload-type resource - e.g. package_show() then package_update()
        with no actual edits, a very common caller pattern used throughout this test file
        (see `update_dict = dict(created_package)` elsewhere) - must NOT be falsely
        flagged into context[FILE_WAS_UPLOADED].

        For url_type == 'upload' resources, model_dictize.resource_dictize() rewrites the
        raw stored 'url' (just the munged filename, e.g. "existing_upload.csv") into a
        fully qualified download URL (e.g. ".../resource/<id>/download/existing_upload.csv")
        whenever the dict isn't built with context['for_edit']=True. Comparing that full
        download URL directly against existing_resource_urls.get(resource_id) (the raw
        filename) would ALWAYS differ - even with zero real change - and wrongly trigger
        DataPusher+ resubmission/datastore churn on every no-op save. package_update()
        must instead unwrap the incoming url via find_filename_in_url() before comparing,
        exactly like the fix does.
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
                   'name': 'test_activity_upload_url_unchanged',
                   'title': 'Test Activity Upload Url Unchanged',
                   'resources': [
                       {
                           'url': 'existing_upload.csv',
                           'url_type': 'upload',
                           'resource_type': 'file.upload',
                           'format': 'CSV',
                           'name': 'existing_upload.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        # Sanity check: package_show() (no for_edit) really does rewrite the raw filename
        # into a fully qualified download URL for upload-type resources - otherwise this
        # test wouldn't actually exercise the unwrapping logic being regression-tested.
        assert existing_resource['url_type'] == 'upload'
        assert existing_resource['url'] != 'existing_upload.csv'
        assert existing_resource['url'].endswith('/existing_upload.csv')

        # No edits at all - just the exact dict package_show() returned, re-saved as-is.
        update_dict = dict(created_package)

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_called_once()
        call_context, _ = mock_manage_datastore.call_args[0]
        assert existing_resource_id not in call_context.get(FILE_WAS_UPLOADED, set())

    def test_package_update_scheme_less_url_round_trip_not_falsely_flagged(self):
        """
        Regression test: model_dictize.resource_dictize() (ckan/lib/dictization/
        model_dictize.py:145-147) unconditionally prepends 'http://' to a stored
        scheme-less url whenever the dict isn't built with context['for_edit']=True -
        exactly the shape of dict a normal package_show() -> edit-something-else ->
        package_update() round trip carries. Comparing that raw, scheme-prefixed
        incoming url directly against existing_resource_urls (the raw, scheme-less DB
        value) would false-flag every such round trip on a scheme-less link resource,
        even when the url itself never actually changed. Both sides must be normalized
        (scheme stripped) via _normalize_resource_url_for_comparison() before comparing.
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
                   'name': 'test_activity_scheme_less_url',
                   'title': 'Test Activity Scheme Less Url',
                   'resources': [
                       {
                           'url': 'example.com/scheme_less.csv',
                           'resource_type': 'url',
                           'format': 'CSV',
                           'name': 'scheme_less.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        # Sanity check: package_show() (no for_edit) really does rewrite a scheme-less
        # stored url into one prefixed with 'http://' - otherwise this test wouldn't
        # actually exercise the scheme-stripping logic being regression-tested.
        assert existing_resource['url'] == 'http://example.com/scheme_less.csv'

        # No edits at all - just the exact dict package_show() returned, re-saved as-is.
        update_dict = dict(created_package)

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_called_once()
        call_context, _ = mock_manage_datastore.call_args[0]
        assert existing_resource_id not in call_context.get(FILE_WAS_UPLOADED, set())

    def test_package_update_stable_url_last_modified_change_reaches_manage_datastore(self):
        """
        Regression test for existing_resource_last_modified: CKAN core's
        resource_dict_save() sets obj.url_changed = True not just on a url change, but
        ALSO when an EXISTING resource's last_modified changes
        (`'last_modified' in changed and not new` - ckan/lib/dictization/
        model_save.py:50-51). A harvester/package_revise call that bumps last_modified
        for content at a STABLE remote url (no url change at all) - to signal "the
        remote content changed, re-fetch me" - must still reach
        _manage_datastore_for_uploads(), now that the IResourceUrlChange hook is an
        intentional no-op.
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
                   'name': 'test_activity_stable_url_last_modified',
                   'title': 'Test Activity Stable Url Last Modified',
                   'resources': [
                       {
                           'url': 'https://example.com/stable_url.csv',
                           'resource_type': 'url',
                           'format': 'CSV',
                           'name': 'stable_url.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        update_dict = dict(created_package)
        # url is UNCHANGED (stable remote url) - only last_modified is bumped, exactly
        # as a harvester would do to signal "the remote content changed".
        new_last_modified = (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat()
        update_dict['resources'] = [dict(existing_resource, last_modified=new_last_modified)]

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert existing_resource_id in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_package['id']

    def test_package_update_upload_resource_filename_change_reaches_manage_datastore(self):
        """
        Counterpart to test_package_update_upload_resource_unchanged_url_not_falsely_flagged:
        an existing url_type == 'upload' resource whose underlying filename genuinely
        changes (e.g. its stored 'url' changes from "existing_upload.csv" to
        "renamed_upload.csv") - even with no 'upload'/'clear_upload' key present in the
        incoming dict - must still be flagged into context[FILE_WAS_UPLOADED] and reach
        _manage_datastore_for_uploads(). This proves find_filename_in_url() unwrapping is
        only used for a like-for-like comparison and doesn't mask genuine changes.
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
                   'name': 'test_activity_upload_url_changed',
                   'title': 'Test Activity Upload Url Changed',
                   'resources': [
                       {
                           'url': 'existing_upload.csv',
                           'url_type': 'upload',
                           'resource_type': 'file.upload',
                           'format': 'CSV',
                           'name': 'existing_upload.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        existing_resource = created_package['resources'][0]
        existing_resource_id = existing_resource['id']

        update_dict = dict(created_package)
        # Same download-url shape as the incoming resource dict would normally carry for
        # an upload-type resource, but with a genuinely different filename at the end -
        # simulating the stored file having actually changed.
        changed_download_url = existing_resource['url'].rsplit('/', 1)[0] + '/renamed_upload.csv'
        update_dict['resources'] = [dict(existing_resource, url=changed_download_url)]

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_called_once()
        call_context, call_package_dict = mock_manage_datastore.call_args[0]
        assert existing_resource_id in call_context.get(FILE_WAS_UPLOADED, set())
        assert call_package_dict.get('id') == created_package['id']

    def test_package_revise_resurrected_deleted_resource_not_treated_as_new(self):
        """

        Regression test for existing_resource_ids being computed from pkg.resources_all
        (ALL states) rather than pkg.resources (which filters out state='deleted').

        CKAN core's resource_dict_save() (ckan/lib/dictization/model_save.py) looks up a
        resource unconditionally by id (session.query(model.Resource).get(id)),
        regardless of its current state - so resurrecting a previously-deleted resource
        id (e.g. via a direct package_revise update__resources__extend call re-adding the
        same id) is treated as an EXISTING resource by core (it just flips its state back
        to 'active'), NOT a new one.

        If existing_resource_ids were computed from pkg.resources instead (which
        excludes deleted resources), the resurrected id would incorrectly be classified
        as "new" here, wrongly flagging it into context[FILE_WAS_UPLOADED] for a
        resource that core itself doesn't consider new.
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
                   'name': 'test_activity_resurrected_resource',
                   'title': 'Test Activity Resurrected Resource',
                   'resources': [
                       {
                           'url': 'https://example.com/to_be_deleted.csv',
                           'resource_type': 'url',
                           'format': 'CSV',
                           'name': 'to_be_deleted.csv',
                       }
                   ]
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)
        resource_id = created_package['resources'][0]['id']

        self._get_action('resource_delete')(context, {'id': resource_id})

        # NOTE: uses a FRESH context for the package_revise call below, deliberately NOT
        # reusing `context` from package_create/resource_delete above. HDX's own
        # resource_delete() (ckanext-hdx_package/ckanext/hdx_package/actions/delete.py)
        # sets context['defer_commit'] = True directly on whatever context it's given
        # and never resets it - so reusing that same context object here would make
        # package_update() skip _manage_datastore_for_uploads() entirely for an unrelated
        # reason, masking what this test is actually meant to verify.
        revise_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        revise_dict = {
            'match': {'id': created_package['id']},
            'update__resources__extend': [{
                'id': resource_id,
                'url': 'https://example.com/to_be_deleted.csv',
                'resource_type': 'url',
                'format': 'CSV',
                'name': 'to_be_deleted.csv',
            }]
        }

        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_revise')(revise_context, revise_dict)

        mock_manage_datastore.assert_called_once()
        call_context, _ = mock_manage_datastore.call_args[0]
        assert resource_id not in call_context.get(FILE_WAS_UPLOADED, set())

    def test_package_update_defer_commit_skips_datastore_management(self):
        """
        Regression test: when context['defer_commit'] is set, package_update() must NOT
        call _manage_datastore_for_uploads(), since the caller hasn't actually committed
        the transaction yet (and may still roll it back) - submitting to DataPusher+ (a
        separate process/worker) at that point could act on a resource that isn't really
        persisted, or later gets rolled back entirely.
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
                   'name': 'test_activity_defer_commit',
                   'title': 'Test Activity Defer Commit'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        update_dict = dict(created_package)
        update_dict['notes'] = 'Updated notes for defer_commit test'

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin',
                           'defer_commit': True}
        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads'
        ) as mock_manage_datastore:
            self._get_action('package_update')(update_context, update_dict)

        mock_manage_datastore.assert_not_called()
        # the caller deferred the commit itself, so make sure to leave the session clean
        # for subsequent tests
        model.repo.commit()

    def test_package_update_datastore_management_failure_does_not_propagate(self):
        """
        Regression test: a transient failure inside _manage_datastore_for_uploads() (e.g.
        DataPusher+/datastore network hiccup) must NOT make an already-committed
        package_update() call fail for the caller - consistent with
        _manage_datastore_for_uploads()'s own fail-open handling of its allowlist lookup.
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
                   'name': 'test_activity_datastore_failure',
                   'title': 'Test Activity Datastore Failure'
                   }

        context = {'ignore_auth': True,
                   'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        created_package = self._get_action('package_create')(context, package)

        update_dict = dict(created_package)
        update_dict['notes'] = 'Updated notes for datastore failure test'

        update_context = {'ignore_auth': True,
                           'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        with mock.patch(
            'ckanext.hdx_package.actions.update._manage_datastore_for_uploads',
            side_effect=Exception('simulated transient DataPusher+/datastore failure')
        ):
            result = self._get_action('package_update')(update_context, update_dict)

        assert result['notes'] == 'Updated notes for datastore failure test'

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

    def test_one_resource_failure_does_not_block_processing_of_others(self):
        """
        Regression test for the per-resource fail-open handling inside
        _manage_datastore_for_uploads()'s loop: a failure while submitting/looking up ONE
        flagged resource (e.g. a transient DataPusher+ webhook error) must NOT prevent
        the remaining flagged resource ids in the same call from being processed.

        Before the fix, only the datastore_delete branch had its own try/except; an
        exception raised anywhere else in the loop (e.g. from _submit_to_datapusher()
        itself) propagated out of the whole `for resource_id in uploaded_resource_ids`
        loop, silently aborting processing of every resource queued after the failing
        one (and getting swallowed by package_update()'s own OUTER try/except, which
        still returns success to the caller).
        """
        import ckan.plugins as ckan_plugins
        from ckanext.hdx_package.actions.update import _manage_datastore_for_uploads
        from ckanext.hdx_package.helpers.constants import FILE_WAS_UPLOADED

        resource_id_fails = 'res-fail'
        resource_id_ok = 'res-ok'

        package_dict = {
            'id': self.PACKAGE_ID,
            'resources': [
                {'id': resource_id_fails, 'format': 'CSV'},
                {'id': resource_id_ok, 'format': 'CSV'},
            ],
        }
        context = {FILE_WAS_UPLOADED: {resource_id_fails, resource_id_ok}}

        fake_dp_plugin = mock.MagicMock()
        fake_dp_plugin.name = 'datapusher_plus'

        def submit_side_effect(resource_dict):
            if resource_dict['id'] == resource_id_fails:
                raise Exception('simulated transient DataPusher+ failure for res-fail')

        fake_dp_plugin._submit_to_datapusher.side_effect = submit_side_effect

        def get_action_side_effect(action_name):
            if action_name == 'hdx_is_package_allowed_for_datastore':
                return lambda ctx, data: True
            return mock.MagicMock()

        with mock.patch(
            'ckanext.hdx_package.actions.update._get_action',
            side_effect=get_action_side_effect
        ), mock.patch(
            'ckanext.hdx_package.actions.update.tk'
        ) as mock_tk, mock.patch.object(
            ckan_plugins, 'PluginImplementations', return_value=[fake_dp_plugin]
        ):
            mock_tk.config.get.side_effect = lambda key, default=None: (
                ['csv', 'xls', 'xlsx', 'tsv'] if 'formats' in key else default
            )
            # Must NOT raise - the failure for resource_id_fails must be caught/logged,
            # and resource_id_ok must still be attempted.
            _manage_datastore_for_uploads(context, package_dict)

        assert fake_dp_plugin._submit_to_datapusher.call_count == 2
        submitted_ids = {
            call.args[0]['id'] for call in fake_dp_plugin._submit_to_datapusher.call_args_list
        }
        assert submitted_ids == {resource_id_fails, resource_id_ok}
