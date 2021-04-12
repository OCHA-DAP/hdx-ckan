from flask import Blueprint

import ckan.plugins.toolkit as tk
import ckan.model as model

g = tk.g
_ = tk._
_get_action = tk.get_action
render = tk.render
abort = tk.abort

NotAuthorized = tk.NotAuthorized

hdx_run_checks = Blueprint(u'hdx_run_checks', __name__, url_prefix=u'/run-checks')


def run_checks():
    context = {
        'model': model, 'session': model.Session,
        'user': g.user, 'auth_user_obj': g.userobj
    }
    try:
        result = _get_action('run_checks')(context, {})
        _compute_render_color(result)
        return render("show_check_results.html", extra_vars={'data': result, 'errors': {}})
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))


def _compute_render_color(checks):
    for check in checks:
        color = 'black'
        if check.get('result') == 'Passed':
            color = 'green'
        elif check.get('result') == 'Failed':
            color = 'red'

        check['render_color'] = color
        if check.get('subchecks'):
            _compute_render_color(check.get('subchecks'))


hdx_run_checks.add_url_rule(u'', view_func=run_checks)
