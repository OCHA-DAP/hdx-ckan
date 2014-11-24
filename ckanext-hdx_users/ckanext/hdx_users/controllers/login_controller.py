import datetime
import dateutil

import ckan.controllers.user as ckan_user
import ckan.lib.helpers as h
import ckan.lib.base as base
from ckan.common import _, c, g, request
import ckan.logic as logic
from pylons import config

get_action = logic.get_action


class LoginController(ckan_user.UserController):

    def logged_in(self):
        # redirect if needed
        came_from = request.params.get('came_from', '')
        if self._sane_came_from(came_from):
            return h.redirect_to(str(came_from))

        if c.user:
            context = None
            data_dict = {'id': c.user}

            user_dict = get_action('user_show')(context, data_dict)

            if 'created' in user_dict:
                time_passed = datetime.datetime.now(
                ) - dateutil.parser.parse(user_dict['created'])
            else:
                time_passed = None
            if not user_dict['activity'] and time_passed and time_passed.days < 3:
                #/dataset/new
                contribute_url = h.url_for(controller='package', action='new')
                # message = ''' Now that you've registered an account , you can <a href="%s">start adding datasets</a>.
                #    If you want to associate this dataset with an organization, either click on "My Organizations" below
                #    to create a new organization or ask the admin of an existing organization to add you as a member.''' % contribute_url
                #h.flash_success(_(message), True)
                return h.redirect_to(controller='user', action='dashboard_organizations')
            else:
                h.flash_success(_("%s is now logged in") %
                                user_dict['display_name'])
                return self.me()
        else:
            err = _('Login failed. Bad username or password.')
            if g.openid_enabled:
                err += _(' (Or if using OpenID, it hasn\'t been associated '
                         'with a user account.)')
            if h.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def contribute(self, error=None):
        self.login(error)
        vars = {'contribute': True}
        return base.render('user/login.html', extra_vars=vars)
