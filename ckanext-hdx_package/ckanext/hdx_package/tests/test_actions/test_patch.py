import json
import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from typing import Dict, cast
from unittest.mock import patch
from ckan.types import Context

from ckanext.hdx_package.helpers.constants import BATCH_MODE, BATCH_MODE_KEEP_OLD
from ckanext.hdx_package.actions.update import SKIP_VALIDATION
from ckanext.hdx_users.helpers.permissions import Permissions

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

SYSADMIN_USER = 'test_hdx_sysadmin_user'
STANDARD_USER = 'test_hdx_standard_user'


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestResourcePatch:
    """Tests for the custom HDX resource_patch action."""

    def test_resource_patch_updates_field(self, dataset_with_uploaded_resource: Dict):
        """resource_patch should update the specified field of the resource."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        new_description = 'Updated description via resource_patch'
        patched = _get_action('resource_patch')(context, {
            'id': resource_id,
            'description': new_description,
        })

        assert patched['description'] == new_description

    def test_resource_patch_preserves_existing_fields(self, dataset_with_uploaded_resource: Dict):
        """resource_patch should preserve fields not mentioned in data_dict (patch semantics)."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']
        original_name = resource_dict['name']
        original_format = resource_dict['format']

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        patched = _get_action('resource_patch')(context, {
            'id': resource_id,
            'description': 'Some description',
        })

        assert patched['name'] == original_name, 'name should be preserved after patch'
        assert patched['format'] == original_format, 'format should be preserved after patch'

    def test_resource_patch_sets_no_compute_extra_hdx_show_properties(self, dataset_with_uploaded_resource: Dict):
        """resource_patch should set no_compute_extra_hdx_show_properties=True in context."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']

        captured_context = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'resource_update':
                def wrapper(ctx, data):
                    captured_context.update(ctx)
                    return original_fn('resource_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('resource_patch')(context, {
                'id': resource_id,
                'description': 'Testing context flag',
            })

        assert captured_context.get('no_compute_extra_hdx_show_properties') is True

    def test_resource_patch_moves_batch_mode_to_context(self, dataset_with_uploaded_resource: Dict):
        """resource_patch should move BATCH_MODE from data_dict into context."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']

        captured_context = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'resource_update':
                def wrapper(ctx, data):
                    captured_context.update(ctx)
                    return original_fn('resource_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('resource_patch')(context, {
                'id': resource_id,
                'description': 'Testing batch mode',
                BATCH_MODE: BATCH_MODE_KEEP_OLD,
            })

        assert captured_context.get(BATCH_MODE) == BATCH_MODE_KEEP_OLD, \
            'BATCH_MODE should have been moved from data_dict to context'

    def test_resource_patch_batch_mode_stripped_from_data_dict(self, dataset_with_uploaded_resource: Dict):
        """BATCH_MODE key should be removed from data_dict before it reaches resource_update."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']

        captured_data_dict = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'resource_update':
                def wrapper(ctx, data):
                    captured_data_dict.update(data)
                    return original_fn('resource_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('resource_patch')(context, {
                'id': resource_id,
                BATCH_MODE: BATCH_MODE_KEEP_OLD,
            })

        assert BATCH_MODE not in captured_data_dict, \
            'BATCH_MODE should have been stripped from data_dict before calling resource_update'

    def test_resource_patch_moves_skip_validation_to_context(self, dataset_with_uploaded_resource: Dict):
        """resource_patch should move SKIP_VALIDATION from data_dict into context."""
        resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource_dict['id']

        captured_context = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'resource_update':
                def wrapper(ctx, data):
                    captured_context.update(ctx)
                    return original_fn('resource_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('resource_patch')(context, {
                'id': resource_id,
                'description': 'Testing skip validation',
                SKIP_VALIDATION: True,
            })

        assert captured_context.get(SKIP_VALIDATION) is True, \
            'SKIP_VALIDATION should have been moved from data_dict to context'


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestPackagePatch:
    """Tests for the custom HDX package_patch action."""

    def test_package_patch_updates_field(self, dataset_with_uploaded_resource: Dict):
        """package_patch should update the specified field of the dataset."""
        dataset_id = dataset_with_uploaded_resource['id']

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        new_notes = 'Updated notes via package_patch'
        patched = _get_action('package_patch')(context, {
            'id': dataset_id,
            'notes': new_notes,
        })

        assert patched['notes'] == new_notes

    def test_package_patch_preserves_existing_fields(self, dataset_with_uploaded_resource: Dict):
        """package_patch should preserve fields not mentioned in data_dict (patch semantics)."""
        dataset_id = dataset_with_uploaded_resource['id']
        original_title = dataset_with_uploaded_resource['title']
        original_owner_org = dataset_with_uploaded_resource['owner_org']

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        patched = _get_action('package_patch')(context, {
            'id': dataset_id,
            'notes': 'Some notes',
        })

        assert patched['title'] == original_title, 'title should be preserved after patch'
        assert patched['owner_org'] == original_owner_org, 'owner_org should be preserved after patch'

    def test_package_patch_preserves_resources(self, dataset_with_uploaded_resource: Dict):
        """package_patch should preserve resources when patching only metadata fields."""
        dataset_id = dataset_with_uploaded_resource['id']
        original_resource_count = len(dataset_with_uploaded_resource['resources'])

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        patched = _get_action('package_patch')(context, {
            'id': dataset_id,
            'notes': 'Patching notes only',
        })

        assert len(patched['resources']) == original_resource_count, \
            'Resources should be preserved when only patching metadata fields'

    def test_package_patch_moves_skip_validation_to_context(self, dataset_with_uploaded_resource: Dict):
        """package_patch should move SKIP_VALIDATION from data_dict into context."""
        dataset_id = dataset_with_uploaded_resource['id']

        captured_context = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'package_update':
                def wrapper(ctx, data):
                    captured_context.update(ctx)
                    return original_fn('package_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('package_patch')(context, {
                'id': dataset_id,
                'notes': 'Testing skip validation',
                SKIP_VALIDATION: True,
            })

        assert captured_context.get(SKIP_VALIDATION) is True, \
            'SKIP_VALIDATION should have been moved from data_dict to context'

    def test_package_patch_skip_validation_stripped_from_data_dict(self, dataset_with_uploaded_resource: Dict):
        """SKIP_VALIDATION key should be removed from data_dict before it reaches package_update."""
        dataset_id = dataset_with_uploaded_resource['id']

        captured_data_dict = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'package_update':
                def wrapper(ctx, data):
                    captured_data_dict.update(data)
                    return original_fn('package_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('package_patch')(context, {
                'id': dataset_id,
                SKIP_VALIDATION: True,
            })

        assert SKIP_VALIDATION not in captured_data_dict, \
            'SKIP_VALIDATION should be stripped from data_dict before calling package_update'

    def test_package_patch_id_taken_from_package_show(self, dataset_with_uploaded_resource: Dict):
        """package_patch should use the id returned by package_show, not the raw input id."""
        dataset_id = dataset_with_uploaded_resource['id']
        dataset_name = dataset_with_uploaded_resource['name']

        captured_data_dict = {}

        import ckanext.hdx_package.actions.patch as patch_module
        original_fn = patch_module._get_action

        def mock_get_action(action_name):
            if action_name == 'package_update':
                def wrapper(ctx, data):
                    captured_data_dict.update(data)
                    return original_fn('package_update')(ctx, data)
                return wrapper
            return original_fn(action_name)

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': SYSADMIN_USER,
        })

        # Pass the dataset name as id (not the UUID); package_patch should resolve it to UUID
        with patch.object(patch_module, '_get_action', side_effect=mock_get_action):
            _get_action('package_patch')(context, {
                'id': dataset_name,
                'notes': 'Patch via name',
            })

        # The id forwarded to package_update should be the UUID from package_show
        assert captured_data_dict.get('id') == dataset_id, \
            'package_patch should resolve dataset name to UUID via package_show'

    def test_package_patch_unauthorized(self, dataset_with_uploaded_resource: Dict):
        """package_patch should raise NotAuthorized for users without edit rights."""
        dataset_id = dataset_with_uploaded_resource['id']

        # Create a user that is not a member of the organization
        non_member = factories.User(name='non_member_pkg_patch', email='non_member_pkg_patch@hdx.hdxtest.org')

        context = cast(Context, {
            'model': model,
            'session': model.Session,
            'user': non_member['name'],
        })

        with pytest.raises(NotAuthorized):
            _get_action('package_patch')(context, {
                'id': dataset_id,
                'notes': 'Should not be allowed',
            })


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxMarkBrokenLinkInResource:
    """Tests for hdx_mark_broken_link_in_resource action."""

    def test_marks_broken_link_true_by_default(self, dataset_with_uploaded_resource: Dict):
        """Calling without explicit broken_link value defaults to True."""
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_broken_link_in_resource')(context, {'id': resource_id})

        package = result.get('package', {})
        updated_resource = next((r for r in package.get('resources', []) if r['id'] == resource_id), None)
        assert updated_resource is not None
        assert updated_resource.get('broken_link') is True

    def test_marks_broken_link_with_explicit_true(self, dataset_with_uploaded_resource: Dict):
        """Explicitly passing broken_link=True marks the resource as broken."""
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_broken_link_in_resource')(
            context, {'id': resource_id, 'broken_link': True})

        package = result.get('package', {})
        updated_resource = next((r for r in package.get('resources', []) if r['id'] == resource_id), None)
        assert updated_resource is not None
        assert updated_resource.get('broken_link') is True

    def test_raises_not_found_without_resource_id(self, dataset_with_uploaded_resource: Dict):
        """Missing resource id should raise NotFound."""
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        with pytest.raises(NotFound):
            _get_action('hdx_mark_broken_link_in_resource')(context, {})


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxMarkQaCompleted:
    """Tests for hdx_mark_qa_completed action."""

    def test_sysadmin_can_mark_qa_completed_true(self, dataset_with_uploaded_resource: Dict):
        """Sysadmin should be able to set qa_completed=True."""
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_qa_completed')(
            context, {'id': dataset_id, 'qa_completed': True})

        assert result is not None
        assert result.get('package', {}).get('qa_completed') is True

    def test_sysadmin_can_unmark_qa_completed(self, dataset_with_uploaded_resource: Dict):
        """Sysadmin should be able to set qa_completed=False."""
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_qa_completed')(
            context, {'id': dataset_id, 'qa_completed': False})

        assert result is not None
        assert result.get('package', {}).get('qa_completed') is False

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        """Standard user without QA permission should be rejected."""
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_mark_qa_completed')(
                context, {'id': dataset_id, 'qa_completed': True})

    def test_raises_validation_error_without_qa_completed_key(
            self, dataset_with_uploaded_resource: Dict):
        """Missing qa_completed key should raise ValidationError via get_or_bust."""
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        with pytest.raises(ValidationError):
            _get_action('hdx_mark_qa_completed')(context, {'id': dataset_id})


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxMarkResourceInQuarantine:
    """Tests for hdx_mark_resource_in_quarantine action."""

    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_sysadmin_can_quarantine_resource(
            self, mock_tag_s3, mock_analytics_cls, dataset_with_uploaded_resource: Dict):
        mock_analytics_cls.return_value.should_send_analytics_event.return_value = False
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_resource_in_quarantine')(
            context, {'id': resource_id, 'in_quarantine': 'true'})

        assert result is not None
        assert result.get('in_quarantine') is True

    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_sysadmin_can_unquarantine_resource(
            self, mock_tag_s3, mock_analytics_cls, dataset_with_uploaded_resource: Dict):
        mock_analytics_cls.return_value.should_send_analytics_event.return_value = False
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_mark_resource_in_quarantine')(
            context, {'id': resource_id, 'in_quarantine': 'false'})

        assert result is not None

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_mark_resource_in_quarantine')(
                context, {'id': resource_id, 'in_quarantine': 'true'})


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxQaResourcePatch:
    """Tests for hdx_qa_resource_patch action."""

    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_sysadmin_can_set_in_quarantine_true(
            self, mock_tag_s3, mock_analytics_cls, dataset_with_uploaded_resource: Dict):
        mock_analytics_cls.return_value.should_send_analytics_event.return_value = False
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_qa_resource_patch')(
            context, {'id': resource_id, 'in_quarantine': 'true'})

        assert result is not None
        assert result.get('in_quarantine') is True

    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_sysadmin_can_set_in_quarantine_false(
            self, mock_tag_s3, mock_analytics_cls, dataset_with_uploaded_resource: Dict):
        mock_analytics_cls.return_value.should_send_analytics_event.return_value = False
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_qa_resource_patch')(
            context, {'id': resource_id, 'in_quarantine': 'false'})

        assert result is not None

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_qa_resource_patch')(
                context, {'id': resource_id, 'in_quarantine': 'true'})


class TestRemoveGeopreviewData:
    """Unit tests for the _remove_geopreview_data private helper (no DB needed)."""

    @patch('ckanext.hdx_package.actions.patch.delete_geopreview_layer')
    def test_removes_shape_info_and_calls_delete_when_quarantining(self, mock_delete):
        from ckanext.hdx_package.actions.patch import _remove_geopreview_data

        data_revise_dict: Dict = {}
        resource_dict = {'id': 'res-abc12345', 'shape_info': 'some_shape_info'}

        _remove_geopreview_data('true', data_revise_dict, resource_dict)

        assert 'filter' in data_revise_dict
        assert any('shape_info' in entry for entry in data_revise_dict['filter'])
        mock_delete.assert_called_once_with('res-abc12345')

    @patch('ckanext.hdx_package.actions.patch.delete_geopreview_layer')
    def test_no_action_when_quarantine_value_is_false(self, mock_delete):
        from ckanext.hdx_package.actions.patch import _remove_geopreview_data

        data_revise_dict: Dict = {}
        resource_dict = {'id': 'res-abc12345', 'shape_info': 'some_shape_info'}

        _remove_geopreview_data('false', data_revise_dict, resource_dict)

        assert 'filter' not in data_revise_dict
        mock_delete.assert_not_called()

    @patch('ckanext.hdx_package.actions.patch.delete_geopreview_layer')
    def test_no_action_when_quarantining_but_no_shape_info(self, mock_delete):
        from ckanext.hdx_package.actions.patch import _remove_geopreview_data

        data_revise_dict: Dict = {}
        resource_dict = {'id': 'res-abc12345'}  # no shape_info

        _remove_geopreview_data('true', data_revise_dict, resource_dict)

        assert 'filter' not in data_revise_dict
        mock_delete.assert_not_called()

    @patch('ckanext.hdx_package.actions.patch.delete_geopreview_layer')
    def test_no_action_when_quarantine_value_is_none(self, mock_delete):
        from ckanext.hdx_package.actions.patch import _remove_geopreview_data

        data_revise_dict: Dict = {}
        resource_dict = {'id': 'res-abc12345', 'shape_info': 'some_shape_info'}

        _remove_geopreview_data(None, data_revise_dict, resource_dict)

        assert 'filter' not in data_revise_dict
        mock_delete.assert_not_called()


class TestDoQuarantineRelatedProcessing:
    """Unit tests for _do_quarantine_related_processing_if_needed (no DB needed)."""

    @patch('ckanext.hdx_package.actions.patch._remove_geopreview_data')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    def test_sends_analytics_and_s3_tag_for_upload_resource(
            self, mock_analytics_cls, mock_tag_s3, mock_remove_geo):
        from ckanext.hdx_package.actions.patch import _do_quarantine_related_processing_if_needed

        mock_analytics = mock_analytics_cls.return_value
        mock_analytics.should_send_analytics_event.return_value = True

        context = {'model': None, 'user': 'admin', 'auth_user_obj': None}
        data_dict = {'id': 'res-1', 'in_quarantine': 'true'}
        data_revise_dict: Dict = {}
        dataset_dict = {'name': 'test-dataset'}
        resource_dict = {'id': 'res-1', 'url_type': 'upload', 'url': 'http://example.com/file.csv'}

        _do_quarantine_related_processing_if_needed(
            context, data_dict, data_revise_dict, dataset_dict, resource_dict)

        mock_analytics_cls.assert_called_once()
        mock_analytics.send_to_queue.assert_called_once()
        mock_tag_s3.assert_called_once()
        mock_remove_geo.assert_called_once()

    @patch('ckanext.hdx_package.actions.patch._remove_geopreview_data')
    @patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    def test_no_s3_tagging_for_non_upload_resource(
            self, mock_analytics_cls, mock_tag_s3, mock_remove_geo):
        from ckanext.hdx_package.actions.patch import _do_quarantine_related_processing_if_needed

        mock_analytics = mock_analytics_cls.return_value
        mock_analytics.should_send_analytics_event.return_value = False

        context = {'model': None, 'user': 'admin', 'auth_user_obj': None}
        data_dict = {'id': 'res-1', 'in_quarantine': 'true'}
        data_revise_dict: Dict = {}
        dataset_dict = {'name': 'test-dataset'}
        resource_dict = {'id': 'res-1', 'url_type': 'api', 'url': 'https://api.example.com'}

        _do_quarantine_related_processing_if_needed(
            context, data_dict, data_revise_dict, dataset_dict, resource_dict)

        mock_analytics_cls.assert_called_once()
        mock_tag_s3.assert_not_called()
        mock_remove_geo.assert_called_once()

    @patch('ckanext.hdx_package.actions.patch._remove_geopreview_data')
    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    def test_no_analytics_when_in_quarantine_not_in_data_dict(
            self, mock_analytics_cls, mock_remove_geo):
        from ckanext.hdx_package.actions.patch import _do_quarantine_related_processing_if_needed

        context = {'model': None, 'user': 'admin', 'auth_user_obj': None}
        data_dict = {'id': 'res-1'}  # no 'in_quarantine' key
        data_revise_dict: Dict = {}
        dataset_dict = {'name': 'test-dataset'}
        resource_dict = {'id': 'res-1', 'url_type': 'upload'}

        _do_quarantine_related_processing_if_needed(
            context, data_dict, data_revise_dict, dataset_dict, resource_dict)

        mock_analytics_cls.assert_not_called()
        # _remove_geopreview_data is always called regardless
        mock_remove_geo.assert_called_once_with(None, data_revise_dict, resource_dict)

    @patch('ckanext.hdx_package.actions.patch._remove_geopreview_data')
    @patch('ckanext.hdx_package.actions.patch.QAQuarantineAnalyticsSender')
    def test_analytics_not_queued_when_should_send_returns_false(
            self, mock_analytics_cls, mock_remove_geo):
        from ckanext.hdx_package.actions.patch import _do_quarantine_related_processing_if_needed

        mock_analytics = mock_analytics_cls.return_value
        mock_analytics.should_send_analytics_event.return_value = False

        context = {'model': None, 'user': 'admin', 'auth_user_obj': None}
        data_dict = {'id': 'res-1', 'in_quarantine': 'true'}
        data_revise_dict: Dict = {}
        dataset_dict = {'name': 'test-dataset'}
        resource_dict = {'id': 'res-1', 'url_type': 'api'}

        _do_quarantine_related_processing_if_needed(
            context, data_dict, data_revise_dict, dataset_dict, resource_dict)

        mock_analytics_cls.assert_called_once()
        mock_analytics.send_to_queue.assert_not_called()


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxFsCheckResourceRevise:
    """Tests for hdx_fs_check_resource_revise action."""

    def test_sysadmin_can_set_fs_check_info(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        package_id = resource['package_id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        fs_check_value = {'state': 'success', 'message': 'Test fs check result'}
        _get_action('hdx_fs_check_resource_revise')(context, {
            'id': resource_id,
            'package_id': package_id,
            'key': 'fs_check_info',
            'value': fs_check_value,
        })

        updated_pkg = _get_action('package_show')(context, {'id': package_id})
        updated_res = next(
            (r for r in updated_pkg['resources'] if r['id'] == resource_id), None)
        assert updated_res is not None
        stored = json.loads(updated_res.get('fs_check_info', '{}'))
        # The validator wraps new values in a list (append-style log); take the last entry
        if isinstance(stored, list):
            stored = stored[-1]
        assert stored.get('message') == 'Test fs check result'
        assert stored.get('state') == 'success'

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_fs_check_resource_revise')(context, {
                'id': resource['id'],
                'package_id': resource['package_id'],
                'key': 'fs_check_info',
                'value': {'state': 'success'},
            })


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxQaPackageReviseResource:
    """Tests for hdx_qa_package_revise_resource action."""

    def test_sysadmin_can_set_field_on_all_resources(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        _get_action('hdx_qa_package_revise_resource')(context, {
            'id': dataset_id,
            'key': 'pii_is_sensitive',
            'value': 'yes',
        })

        pkg_dict = _get_action('package_show')(context, {'id': dataset_id})
        for resource in pkg_dict.get('resources', []):
            # The boolean_validator in the resource schema converts 'yes' -> True
            assert resource.get('pii_is_sensitive') is True, \
                f'Resource {resource["id"]} should have pii_is_sensitive set'

    def test_raises_not_found_when_key_or_value_missing(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        with pytest.raises(NotFound):
            _get_action('hdx_qa_package_revise_resource')(context, {
                'id': dataset_id,
                # 'key' and 'value' intentionally omitted
            })

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_qa_package_revise_resource')(context, {
                'id': dataset_id,
                'key': 'pii_is_sensitive',
                'value': 'yes',
            })


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxFsCheckResourceReset:
    """Tests for hdx_fs_check_resource_reset action."""

    def test_sysadmin_resets_fs_check_info_to_empty_string(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        package_id = resource['package_id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        # First set a value via hdx_fs_check_resource_revise
        _get_action('hdx_fs_check_resource_revise')(context, {
            'id': resource_id,
            'package_id': package_id,
            'key': 'fs_check_info',
            'value': {'state': 'processing', 'message': 'Some check started'},
        })

        # Now reset it
        _get_action('hdx_fs_check_resource_reset')(context, {
            'id': resource_id,
            'package_id': package_id,
        })

        updated_pkg = _get_action('package_show')(context, {'id': package_id})
        updated_res = next(
            (r for r in updated_pkg['resources'] if r['id'] == resource_id), None)
        assert updated_res is not None
        assert updated_res.get('fs_check_info') == ''

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_fs_check_resource_reset')(context, {
                'id': resource['id'],
                'package_id': resource['package_id'],
            })


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxFsCheckPackageReset:
    """Tests for hdx_fs_check_package_reset action."""

    def test_sysadmin_resets_all_resources_fs_check_info(self, dataset_with_uploaded_resource: Dict):
        package_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        # Set fs_check_info on each resource first
        for resource in dataset_with_uploaded_resource['resources']:
            _get_action('hdx_fs_check_resource_revise')(context, {
                'id': resource['id'],
                'package_id': package_id,
                'key': 'fs_check_info',
                'value': {'state': 'processing'},
            })

        # Reset all resources
        _get_action('hdx_fs_check_package_reset')(context, {'package_id': package_id})

        updated_pkg = _get_action('package_show')(context, {'id': package_id})
        for resource in updated_pkg.get('resources', []):
            assert resource.get('fs_check_info') == '', \
                f'fs_check_info should be empty for resource {resource["id"]} after package reset'

    def test_raises_not_authorized_for_standard_user(self, dataset_with_uploaded_resource: Dict):
        package_id = dataset_with_uploaded_resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_fs_check_package_reset')(context, {'package_id': package_id})


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxPCodedResourceUpdate:
    """Tests for hdx_p_coded_resource_update action."""

    def test_sysadmin_can_set_p_coded(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        result = _get_action('hdx_p_coded_resource_update')(
            context, {'id': resource_id, 'p_coded': True})

        assert result is not None
        assert result.get('p_coded') is True

    def test_standard_user_with_permission_can_set_p_coded(
            self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        sysadmin_ctx = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})
        user_ctx = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        Permissions(STANDARD_USER).set_permissions(
            sysadmin_ctx, [Permissions.PERMISSION_MANAGE_P_CODES])

        result = _get_action('hdx_p_coded_resource_update')(
            user_ctx, {'id': resource_id, 'p_coded': True})

        assert result is not None
        assert result.get('p_coded') is True

    def test_raises_not_authorized_for_user_without_permission(
            self, dataset_with_uploaded_resource: Dict):
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        no_perm_user = factories.User(name='user_no_pcodes', email='user_no_pcodes@hdx.hdxtest.org')
        context = cast(Context, {'model': model, 'session': model.Session, 'user': no_perm_user['name']})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_p_coded_resource_update')(
                context, {'id': resource_id, 'p_coded': True})


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestHdxMarkResourceInHapi:
    """Tests for hdx_mark_resource_in_hapi action."""

    def test_sysadmin_can_set_in_hapi_flag(self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        _get_action('hdx_mark_resource_in_hapi')(context, {'id': resource_id, 'in_hapi': 'yes'})

        pkg_dict = _get_action('package_show')(context, {'id': resource['package_id']})
        updated = next((r for r in pkg_dict['resources'] if r['id'] == resource_id), None)
        assert updated is not None
        assert updated.get('in_hapi') == 'yes'

    def test_raises_not_found_when_id_or_in_hapi_missing(self, dataset_with_uploaded_resource: Dict):
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})

        with pytest.raises(NotFound):
            _get_action('hdx_mark_resource_in_hapi')(context, {})

    def test_raises_not_authorized_for_user_without_permission(
            self, dataset_with_uploaded_resource: Dict):
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        no_perm_user = factories.User(name='user_no_hapi', email='user_no_hapi@hdx.hdxtest.org')
        context = cast(Context, {'model': model, 'session': model.Session, 'user': no_perm_user['name']})

        with pytest.raises(NotAuthorized):
            _get_action('hdx_mark_resource_in_hapi')(
                context, {'id': resource_id, 'in_hapi': 'yes'})

    def test_standard_user_with_permission_can_set_in_hapi(
            self, dataset_with_uploaded_resource: Dict):
        resource = dataset_with_uploaded_resource['resources'][0]
        resource_id = resource['id']
        sysadmin_ctx = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})
        user_ctx = cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})

        Permissions(STANDARD_USER).set_permissions(
            sysadmin_ctx, [Permissions.PERMISSION_MANAGE_IN_HAPI_FLAG])

        _get_action('hdx_mark_resource_in_hapi')(user_ctx, {'id': resource_id, 'in_hapi': 'yes'})

        pkg_dict = _get_action('package_show')(user_ctx, {'id': resource['package_id']})
        updated = next((r for r in pkg_dict['resources'] if r['id'] == resource_id), None)
        assert updated is not None
        assert updated.get('in_hapi') == 'yes'

