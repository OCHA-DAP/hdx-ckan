from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import g
from ckan.views.user import PerformResetView

render = tk.render
abort = tk.abort
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
h = tk.h
_ = tk._

redirect = tk.redirect_to

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound

user = Blueprint(u'hdx_user', __name__)


class HDXPerformResetView(PerformResetView):

    def get(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': id,
            u'keep_email': True
        }

        g.reset_key = request.params.get(u'key')
        try:
            check_access(u'user_update', context, {
                'id': id,
                'reset_key': g.reset_key,
            })
        except NotAuthorized:
            msg = _(u'The link you accessed is either invalid or has expired. Please request another reset link. '
                    u'If the problem persists please '
                    u'<a href="/faq#auto-faq-Contact-How_do_I_contact_the_HDX_team_-a">contact us</a>.')
            h.flash(msg, category='alert-error', allow_html=True)

        try:
            user_dict = get_action(u'user_show')(context, {u'id': id})
        except NotFound:
            abort(404, _(u'User not found'))

        return render(u'user/perform_reset.html', {
            u'user_dict': user_dict
        })


user.add_url_rule(
    u'/user/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))
