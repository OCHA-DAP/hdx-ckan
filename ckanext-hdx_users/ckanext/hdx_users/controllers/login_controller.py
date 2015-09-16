"""
    Handles modifications to registration and login flow. 
    Including password reset, logging in and redirecting user
    to the correct contribute page when not logged in.

    This is different from modifications to the registration
    and login flow made to add email validation to account
    creation. That class is in mail_validation_controller.py 
"""
import datetime
import dateutil
import json

import ckan.controllers.user as ckan_user
import ckan.lib.helpers as h
import ckan.lib.base as base
import ckan.lib.mailer as mailer
from ckan.common import _, c, g, request
import ckan.logic as logic
from pylons import config
import ckan.model as model
import mail_validation_controller as hdx_mail_c

render = base.render

get_action = logic.get_action
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound
check_access = logic.check_access
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})

class LoginController(ckan_user.UserController):

    def request_reset(self):
        """
        Email password reset instructions to user
        """
        context = {'model': model, 'session': model.Session, 'user': c.user,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': request.params.get('user')}
        try:
            check_access('request_reset', context)
        except NotAuthorized:
            base.abort(401, _('Unauthorized to request reset password.'))

        if request.method == 'POST':
            id = request.params.get('user')

            context = {'model': model,
                       'user': c.user}

            data_dict = {'id': id}
            user_obj = None
            try:
                user_dict = get_action('user_show')(context, data_dict)
                user_obj = context['user_obj']
            except NotFound:
                return hdx_mail_c.OnbUserNotFound
                # h.flash_error(_('No such user: %s') % id)

            if user_obj:
                try:
                    mailer.send_reset_link(user_obj)
                    # h.flash_success(_('Please check your inbox for '
                    #                 'a reset code.'))
                    # h.redirect_to(controller='user',
                    #           action='login', came_from=None)
                    return hdx_mail_c.OnbSuccess
                except mailer.MailerException, e:
                    return OnbResetLinkErr
                    # h.flash_error(_('Could not send reset link: %s') %
                    #               unicode(e))
        # return render('user/request_reset.html')
        return render('home/index.html')

    def logged_in(self):
        """
        Logs user in but directs to different templates depending
        on the user's activity level.
        """
        # redirect if needed
        came_from = request.params.get('came_from', '')
        if h.url_is_local(came_from):
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
            if not (user_dict['number_created_packages'] > 0 or user_dict['number_of_edits'] > 0) and time_passed and time_passed.days < 3:
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
            if h.asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def contribute(self, error=None):
        """
        If the user tries to add data but isn't logged in, directs
        them to a specific contribute login page.
        """
        self.login(error)
        vars = {'contribute': True}
        return base.render('user/login.html', extra_vars=vars)
