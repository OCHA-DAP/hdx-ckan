from typing import Dict, cast
from unittest import mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_theme.tests.conftest import STANDARD_USER, SYSADMIN_USER, UserToken

_get_action = tk.get_action


def _sysadmin_context() -> Context:
    return cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})


def _failing_purge_commit():
    return mock.patch.object(model.repo, 'commit_and_remove', side_effect=SQLAlchemyError('simulated purge failure'))


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

    def test_failed_purge_raises(self, dataset_with_uploaded_resource: Dict):
        dataset_id = dataset_with_uploaded_resource['id']

        with _failing_purge_commit() as mock_commit, pytest.raises(SQLAlchemyError):
            _get_action('hdx_dataset_purge')(_sysadmin_context(), {'id': dataset_id})

        mock_commit.assert_called_once()
        _assert_dataset_kept_as_deleted(dataset_id)

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
