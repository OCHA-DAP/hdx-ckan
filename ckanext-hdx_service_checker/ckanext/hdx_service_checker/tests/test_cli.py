import json

import pytest
from click.testing import CliRunner

from ckanext.hdx_service_checker import cli

PASSED = {'type': 'Dummy Check', 'result': 'Passed', 'error_message': None, 'subchecks': []}
FAILED = {'type': 'Dummy Check', 'result': 'Failed', 'error_message': 'boom', 'subchecks': []}


def _proxy(*subchecks):
    return {'type': 'Proxy Check', 'result': 'subchecks', 'error_message': None, 'subchecks': list(subchecks)}


@pytest.mark.parametrize('checks, expected_exit_code', [
    ([PASSED, _proxy(PASSED)], 0),
    ([PASSED, FAILED], 1),
    ([PASSED, _proxy(PASSED, _proxy(FAILED))], 1),
], ids=['all-passed', 'top-level-failure', 'nested-failure'])
def test_run_outputs_json_and_exit_code(monkeypatch, checks, expected_exit_code):
    monkeypatch.setattr(cli.tk, 'get_action', lambda name: lambda context, data_dict: checks)

    result = CliRunner().invoke(cli.run)

    assert json.loads(result.output) == checks
    assert result.exit_code == expected_exit_code
