from typing import Dict, cast
from unittest import mock

import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.datastore.tests.conftest import clean_datastore  # noqa: F401 (pytest fixture)
from ckanext.hdx_package.actions import get as hdx_get
from ckanext.hdx_package.helpers.analytics import DatastoreApiCallAnalyticsSender
from ckanext.hdx_theme.tests.conftest import (
    DATASET_NAME, LOCATION_NAME, ORG_NAME, SYSADMIN_USER, UserToken,
)

_get_action = tk.get_action

GET_MODULE = 'ckanext.hdx_package.actions.get'


def _call_wrapper(core_result: Dict) -> Dict:
    return hdx_get.datastore_search_sql(lambda context, data_dict: core_result, {'user': 'some_user'},
                                        {'sql': 'SELECT 1'})


class TestDatastoreSearchSqlWrapper:
    """Unit tests for the HDX datastore_search_sql wrapper (no DB needed)."""

    @mock.patch(f'{GET_MODULE}._get_information_needed_for_analytics', return_value=('some_user', 'token'))
    @mock.patch(f'{GET_MODULE}.DatastoreApiCallAnalyticsSender')
    def test_schema_name_tuples_are_sent_as_resource_id_strings(self, mock_sender_cls, _mock_info):
        """CKAN 2.11.7 gives a set of (schema, name) tuples; the sender must get plain resource ids."""
        result = _call_wrapper({'records': [], 'datastore_table_names': {(None, 'res-b'), ('public', 'res-a')}})

        mock_sender_cls.assert_called_once_with('some_user', ['res-a', 'res-b'], 'token', 'datastore_search_sql')
        mock_sender_cls.return_value.send_to_queue.assert_called_once()
        assert 'datastore_table_names' not in result

    @mock.patch(f'{GET_MODULE}._get_information_needed_for_analytics', return_value=('some_user', 'token'))
    @mock.patch(f'{GET_MODULE}.DatastoreApiCallAnalyticsSender')
    def test_string_table_names_are_still_accepted(self, mock_sender_cls, _mock_info):
        _call_wrapper({'records': [], 'datastore_table_names': ['res-a']})

        mock_sender_cls.assert_called_once_with('some_user', ['res-a'], 'token', 'datastore_search_sql')

    @mock.patch(f'{GET_MODULE}._get_information_needed_for_analytics', return_value=('some_user', 'token'))
    @mock.patch(f'{GET_MODULE}.DatastoreApiCallAnalyticsSender')
    def test_no_tables_sends_nothing(self, mock_sender_cls, _mock_info):
        result = _call_wrapper({'records': [], 'datastore_table_names': set()})

        mock_sender_cls.assert_not_called()
        assert 'datastore_table_names' not in result

    @mock.patch(f'{GET_MODULE}._get_information_needed_for_analytics', side_effect=RuntimeError('boom'))
    @mock.patch(f'{GET_MODULE}.DatastoreApiCallAnalyticsSender')
    def test_analytics_failure_still_removes_table_names(self, mock_sender_cls, _mock_info):
        """If analytics fails, the request succeeds and the (non JSON-serialisable) set is not in the response."""
        result = _call_wrapper({'records': [{'a': 1}], 'datastore_table_names': {(None, 'res-a')}})

        mock_sender_cls.assert_not_called()
        assert result == {'records': [{'a': 1}]}


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'clean_datastore')
class TestDatastoreSearchSqlAnalytics:
    """End-to-end: real core search_sql (with the HDX patch) through the API."""

    @mock.patch.object(DatastoreApiCallAnalyticsSender, 'send_to_queue', autospec=True)
    def test_mixpanel_event_has_resource_dataset_org_and_location(
            self, mock_send_to_queue, app, dataset_with_uploaded_resource: Dict,
            sysadmin_user_with_token: UserToken):
        resource_id = dataset_with_uploaded_resource['resources'][0]['id']
        context = cast(Context, {'model': model, 'session': model.Session, 'user': SYSADMIN_USER})
        _get_action('datastore_create')(context, {
            'resource_id': resource_id,
            'force': True,
            'fields': [{'id': 'value', 'type': 'int'}],
            'records': [{'value': 1}],
        })

        res = app.post('/api/action/datastore_search_sql', json={'sql': f'SELECT * FROM "{resource_id}"'},
                       headers={'Authorization': sysadmin_user_with_token.token})

        assert res.status_code == 200, res.get_data(as_text=True)[:600]
        result = res.json['result']
        assert result['records'][0]['value'] == 1
        assert 'datastore_table_names' not in result

        mock_send_to_queue.assert_called_once()
        mp_meta = mock_send_to_queue.call_args.args[0].analytics_dict['mixpanel_meta']
        assert mp_meta['action name'] == 'datastore_search_sql'
        assert mp_meta['resource ids'] == [resource_id]
        assert mp_meta['resource names'] == [dataset_with_uploaded_resource['resources'][0]['name']]
        assert mp_meta['dataset names'] == [DATASET_NAME]
        assert mp_meta['org names'] == [ORG_NAME]
        assert mp_meta['group names'] == [LOCATION_NAME]
