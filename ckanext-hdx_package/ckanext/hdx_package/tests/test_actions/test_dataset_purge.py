from typing import Dict, cast
from unittest import mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context
from ckanext.datastore.backend import DatastoreBackend

from ckanext.hdx_theme.tests.conftest import STANDARD_USER, SYSADMIN_USER, UserToken

_get_action = tk.get_action


def _sysadmin_context() -> Context:
    return cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})


def _editor_context() -> Context:
    """STANDARD_USER is an editor of the dataset's organization"""
    return cast(Context, {'model': model, 'session': model.Session, 'user': STANDARD_USER})


def _failing_purge_commit():
    return mock.patch.object(model.repo, 'commit_and_remove', side_effect=SQLAlchemyError('simulated purge failure'))


def _mock_file_remove(**kwargs):
    return mock.patch('ckanext.hdx_package.actions.delete.file_remove', **kwargs)


def _assert_dataset_kept_as_deleted(dataset_id: str) -> None:
    # Discard the uncommitted purge, as the end of a real request would
    model.Session.rollback()
    pkg = model.Package.get(dataset_id)
    assert pkg is not None
    assert pkg.state == 'deleted'


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index')
class TestDatasetPurge:

    def test_purge_removes_collaborators(self, dataset_with_uploaded_resource: Dict):
        """hdx_dataset_purge runs package_delete first, which already drops collaborators; dataset_purge doesn't."""
        dataset_id = dataset_with_uploaded_resource['id']
        model.Session.add(model.PackageMember(package_id=dataset_id, user_id=model.User.get(STANDARD_USER).id,
                                              capacity='editor'))
        model.Session.commit()

        _get_action('dataset_purge')(_sysadmin_context(), {'id': dataset_id})

        assert model.Package.get(dataset_id) is None
        assert model.Session.query(model.PackageMember).filter_by(package_id=dataset_id).count() == 0

    def test_dataset_purge_is_sysadmin_only(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']

        with pytest.raises(tk.NotAuthorized):
            _get_action('dataset_purge')(_editor_context(), {'id': dataset_id})

        assert model.Package.get(dataset_id).state == 'active'

    def test_editor_purge_removes_files_and_datastore_after_purge_is_committed(
            self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']
        resource = dataset_with_uploaded_resource['resources'][0]
        _get_action('datastore_create')(_sysadmin_context(), {
            'resource_id': resource['id'], 'force': True, 'fields': [{'id': 'a', 'type': 'text'}],
            'records': [{'a': 'x'}],
        })
        backend = DatastoreBackend.get_active_backend()
        assert backend.resource_exists(resource['id'])

        def _assert_dataset_purged(*args):
            assert model.Package.get(dataset_id) is None

        with _mock_file_remove(side_effect=_assert_dataset_purged) as mock_file_remove:
            _get_action('hdx_dataset_purge')(_editor_context(), {'id': dataset_id})

        # The model keeps the uploaded file name; the dict shows the download url
        mock_file_remove.assert_called_once_with(resource['id'], 'hdx_test.csv', 'upload')
        assert not backend.resource_exists(resource['id'])

    def test_failed_purge_raises(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']

        with _failing_purge_commit() as mock_commit, _mock_file_remove() as mock_file_remove, \
                pytest.raises(SQLAlchemyError):
            _get_action('hdx_dataset_purge')(_sysadmin_context(), {'id': dataset_id})

        mock_commit.assert_called_once()
        mock_file_remove.assert_not_called()
        _assert_dataset_kept_as_deleted(dataset_id)

    def test_delete_page_cancel_keeps_dataset(
            self, app, dataset_with_uploaded_resource: Dict, sysadmin_user_with_token: UserToken):
        dataset_id = dataset_with_uploaded_resource['id']

        res = app.post(f'/dataset/delete/{dataset_id}', data={'cancel': ''},
                       headers={'Authorization': sysadmin_user_with_token.token}, follow_redirects=False)

        assert res.status_code == 302
        assert res.headers['Location'].endswith(f'/contribute/edit/{dataset_id}')
        assert model.Package.get(dataset_id).state == 'active'

    def test_delete_page_does_not_report_success_when_purge_fails(
            self, app, dataset_with_uploaded_resource: Dict, sysadmin_user_with_token: UserToken):
        dataset_id = dataset_with_uploaded_resource['id']

        with _failing_purge_commit() as mock_commit:
            res = app.post(f'/dataset/delete/{dataset_id}', headers={'Authorization': sysadmin_user_with_token.token},
                           follow_redirects=False)

        mock_commit.assert_called_once()
        assert res.status_code == 500
        _assert_dataset_kept_as_deleted(dataset_id)

    def test_api_returns_error_when_purge_fails(
            self, app, dataset_with_uploaded_resource: Dict, sysadmin_user_with_token: UserToken):
        """The contribute flow deletes through this API call and shows the error it returns."""
        dataset_id = dataset_with_uploaded_resource['id']

        with _failing_purge_commit() as mock_commit:
            res = app.post('/api/action/hdx_dataset_purge', json={'id': dataset_id},
                           headers={'Authorization': sysadmin_user_with_token.token})

        mock_commit.assert_called_once()
        assert res.status_code == 500
        assert res.json['success'] is False
        _assert_dataset_kept_as_deleted(dataset_id)
