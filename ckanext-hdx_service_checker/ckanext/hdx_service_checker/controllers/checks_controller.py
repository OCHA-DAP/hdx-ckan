import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model

from ckan.common import c, _


class ChecksController(base.BaseController):
    def run_checks(self):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author, 'auth_user_obj': c.userobj
        }
        try:
            result = logic.get_action('run_checks')(context, {})
        except logic.NotAuthorized:
            base.abort(401, _('Not authorized to see this page'))

        self._compute_render_color(result)
        return base.render("show_check_results.html", extra_vars={'data': result, 'errors': {}})

    def _compute_render_color(self, checks):
        for check in checks:
            color = 'black'
            if check.get('result') == 'Passed':
                color = 'green'
            elif check.get('result') == 'Failed':
                color = 'red'

            check['render_color'] = color
            if check.get('subchecks'):
                self._compute_render_color(check.get('subchecks'))