"""
Tests for _handle_datastore_on_resource_update (HDXTABLE-119).

The function is tested directly (unit-style) so no real datastore or
datapusher infrastructure is needed — only the DB model and the two
external calls are mocked.
"""
import pytest
from unittest.mock import MagicMock, patch, call

import ckan.plugins as plugins

from ckanext.hdx_package.actions.update import _handle_datastore_on_resource_update

RESOURCE_ID = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'


def _make_context():
    """Return a minimal context with a mocked model."""
    mock_res = MagicMock()
    mock_res.extras = {'datastore_active': True}

    mock_model = MagicMock()
    mock_model.Resource.get.return_value = mock_res

    return {'model': mock_model, 'user': 'testsysadmin'}


class TestHandleDatastoreOnResourceUpdate:

    # ------------------------------------------------------------------
    # Bug 1 — format changed to unsupported type (e.g. CSV → PDF)
    # ------------------------------------------------------------------

    def test_unsupported_format_with_active_datastore_deletes_table(self, ckan_config):
        """datastore_delete is called and datastore_active flag is cleared."""
        ckan_config['ckan.datapusher.formats'] = ['csv', 'xls', 'xlsx']

        context = _make_context()
        resource = {'id': RESOURCE_ID, 'format': 'PDF', 'url': 'http://example.org/report.pdf'}

        mock_delete = MagicMock()
        with patch('ckanext.hdx_package.actions.update._get_action', return_value=mock_delete):
            _handle_datastore_on_resource_update(
                context, RESOURCE_ID, {}, resource,
                old_datastore_active=True,
                old_url='http://example.org/data.csv',
            )

        mock_delete.assert_called_once_with(
            {'ignore_auth': True},
            {'resource_id': RESOURCE_ID, 'force': True},
        )
        context['model'].Session.commit.assert_called_once()

    def test_unsupported_format_without_active_datastore_is_noop(self, ckan_config):
        """No active datastore → nothing to clean up, datastore_delete not called."""
        ckan_config['ckan.datapusher.formats'] = ['csv', 'xls', 'xlsx']

        context = _make_context()
        resource = {'id': RESOURCE_ID, 'format': 'PDF', 'url': 'http://example.org/report.pdf'}

        with patch('ckanext.hdx_package.actions.update._get_action') as mock_get_action:
            _handle_datastore_on_resource_update(
                context, RESOURCE_ID, {}, resource,
                old_datastore_active=False,
                old_url='http://example.org/data.csv',
            )
            mock_get_action.assert_not_called()

    # ------------------------------------------------------------------
    # Bug 2 — same supported format, file replaced (e.g. CSV → CSV)
    # ------------------------------------------------------------------

    def test_supported_format_with_url_change_triggers_datapusher(self, ckan_config):
        """URL changed → datapusher submitted with the fresh resource dict."""
        ckan_config['ckan.datapusher.formats'] = ['csv', 'xls', 'xlsx']

        context = _make_context()
        resource = {'id': RESOURCE_ID, 'format': 'CSV', 'url': 'http://example.org/new.csv'}

        mock_dp = MagicMock()
        mock_dp.name = 'datapusher_plus'

        with patch('ckanext.hdx_package.actions.update.plugins') as mock_plugins:
            mock_plugins.PluginImplementations.return_value = [mock_dp]
            mock_plugins.IResourceController = plugins.IResourceController

            _handle_datastore_on_resource_update(
                context, RESOURCE_ID, {}, resource,
                old_datastore_active=True,
                old_url='http://example.org/old.csv',  # URL changed
            )

        mock_dp._submit_to_datapusher.assert_called_once_with(resource)

    def test_supported_format_metadata_only_edit_skips_datapusher(self, ckan_config):
        """No upload and URL unchanged → metadata-only edit, datapusher not triggered."""
        ckan_config['ckan.datapusher.formats'] = ['csv', 'xls', 'xlsx']

        context = _make_context()
        same_url = 'http://example.org/data.csv'
        resource = {'id': RESOURCE_ID, 'format': 'CSV', 'url': same_url}

        mock_dp = MagicMock()
        mock_dp.name = 'datapusher_plus'

        with patch('ckanext.hdx_package.actions.update.plugins') as mock_plugins:
            mock_plugins.PluginImplementations.return_value = [mock_dp]
            mock_plugins.IResourceController = plugins.IResourceController

            _handle_datastore_on_resource_update(
                context, RESOURCE_ID, {},  # no 'upload' key
                resource,
                old_datastore_active=True,
                old_url=same_url,  # URL unchanged
            )

        mock_dp._submit_to_datapusher.assert_not_called()
