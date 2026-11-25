import json
import sys

import click
import ckan.plugins.toolkit as tk


def _has_failures(checks):
    return any(
        c.get('result') == 'Failed' or _has_failures(c.get('subchecks') or [])
        for c in checks
    )


@click.group(name='hdx-checks', short_help='HDX service checks')
def hdx_checks():
    pass


@hdx_checks.command('run', short_help='Run all configured service checks')
def run():
    result = tk.get_action('run_checks')({'ignore_auth': True, 'user': ''}, {})
    click.echo(json.dumps(result, indent=2, default=str))
    sys.exit(1 if _has_failures(result) else 0)
