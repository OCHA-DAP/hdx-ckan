import datetime
import logging as logging

import dateutil
from six.moves.urllib.parse import quote

import ckan.model as model
import ckan.plugins as p
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.tokens as tokens
import ckanext.hdx_users.helpers.user_extra as ue_helpers
from ckanext.hdx_users.views.user_view_helper import *

abort = tk.abort
render = tk.render
log = logging.getLogger(__name__)
unflatten = dictization_functions.unflatten
_validate = dictization_functions.validate
ValidationError = tk.ValidationError
check_access = tk.check_access
get_action = tk.get_action
g = tk.g
request = tk.request
_ = tk._
config = tk.config
h = tk.h
asbool = tk.asbool

class HDXUserAuthView:
    def __init__(self):
        pass

    def logged_out_page(self):
        template_data = ue_helpers.get_logout(True, _('User logged out with success'))
        return render('home/index.html', extra_vars=template_data)

    def logged_in(self):

        came_from = request.args.get('came_from', '')
        if h.url_is_local(came_from):
            g.login_came_from = came_from
        else:
            came_from = None

        if g.user:
            context = None
            data_dict = {'id': g.user}
            user_dict = get_action('user_show')(context, data_dict)

            # IAuthenticator too buggy, doing this instead
            try:
                token = tokens.token_show(context, user_dict)
            except NotFound as e:
                token = {'valid': True}  # Until we figure out what to do with existing users
            except:
                abort(500, _('Something wrong'))
            if not token['valid']:
                # force logout
                for item in p.PluginImplementations(p.IAuthenticator):
                    item.logout()
                # redirect to validation page
                h.flash_error(_('You have not yet validated your email.'))
                h.redirect_to(self._get_repoze_handler('logout_handler_path'))

            if 'created' in user_dict:
                time_passed = datetime.datetime.now() - dateutil.parser.parse(user_dict['created'])
            else:
                time_passed = None
            if 'activity' in user_dict and (not user_dict['activity']) and time_passed and time_passed.days < 3:
                # /dataset/new
                # contribute_url = h.url_for(controller='package', action='new')

                return h.redirect_to('dashboard.organizations')
            else:
                userobj = g.userobj if g.userobj else model.User.get(g.user)
                login_dict = {'display_name': userobj.display_name, 'email': userobj.email,
                              'email_hash': userobj.email_hash, 'login': userobj.name}

                max_age = int(14 * 24 * 3600)
                # response.set_cookie('hdx_login', quote(json.dumps(login_dict)), max_age=max_age)
                if not g.user:
                    h.redirect_to(locale=None, controller='user', action='login', id=None)

                # do we need this?
                # user_ref = c.userobj.get_reference_preferred_for_uri()

                _ckan_site_url = config.get('ckan.site_url', '#')
                _came_from = str(came_from or _ckan_site_url)

                excluded_paths = ['/user/validate/', 'user/logged_in?__logins', 'user/logged_out_redirect']

                h.flash_success(_("%s is now logged in") % user_dict['display_name'])
                g.pop('login_came_from', '')
                if _ckan_site_url != _came_from and not any(path in _came_from for path in excluded_paths):
                    res = h.redirect_to(_came_from)
                else:
                    res = h.redirect_to('hdx_dataset.search', locale=None)
                res.set_cookie('hdx_login', quote(json.dumps(login_dict)), max_age=max_age, secure=True)
                return res
        else:
            err = _('Login failed. Bad username or password.')
            try:
                if g.openid_enabled:
                    err += _(' (Or if using OpenID, it hasn\'t been associated '
                             'with a user account.)')
            except:
                pass

            template_data = ue_helpers.get_login(False, err)
            log.error("Status code 401 : username or password incorrect")

            result = render('home/index.html', extra_vars=template_data)
            g.pop('login_came_from', '')
            return result

    def new_login(self, error=None, info_message=None, page_subtitle=None):
        template_data = {}
        if not g.user:
            template_data = ue_helpers.get_login(True, "")
        if info_message:
            if 'data' not in template_data:
                template_data['data'] = {}
            template_data['data']['info_message'] = info_message
            template_data['data']['page_subtitle'] = page_subtitle
        return render('home/index.html', extra_vars=template_data)

