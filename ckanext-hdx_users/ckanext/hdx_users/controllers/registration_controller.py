import ckan.lib.base as base
import ckan.controllers.user
from ckan.common import _, c, request
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.lib.base as base
import ckan.controllers.user
from ckan.common import _, c, request
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.model as model
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.lib.captcha as captcha
import ckan.new_authz as new_authz
import pylons.configuration as configuration
import re
import ckan.lib.navl.dictization_functions as df
import ckan.lib.maintain as maintain
from urllib import quote
import ckan.plugins as p


from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
abort = base.abort
check_access = logic.check_access
get_action = logic.get_action
render = base.render
NotFound = logic.NotFound
ValidationError = logic.ValidationError
DataError = dictization_functions.DataError
NotAuthorized = logic.NotAuthorized
unflatten = dictization_functions.unflatten

Invalid = df.Invalid

@maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
def send_mail(name, email, org, reason = ''):
    ''' The functionality of sending emails with new user requests has been deprecated.
        Deprecated since 13.08.2014 - hdx 0.3.6 
    '''
    body = 'New user registration request\n' \
           'Full Name: {fn}\n' \
           'Email: {mail}\n' \
           'Organisation: {org}\n' \
           'Reason: {reason}\n' \
           '(This is an automated mail)' \
           ''.format(fn=name, mail=email, org=org, reason=reason)

    mailer.mail_recipient("HDX Registration", "vagrant@ckan.lo", "New user registration", body)

    return

#
def name_validator_with_changed_msg(val, context):
    """This is just a wrapper function around the validator.name_validator function. 
        The wrapper function just changes the message in case the name_match doesn't match.
        The only purpose for still calling that function here is to keep the link visible and
        in case of a ckan upgrade to still be able to raise any new Invalid exceptions

    """
    try:
        return name_validator(val, context)
    except Invalid as invalid:
        if val in ['new', 'edit', 'search']:
            raise Invalid(_('That name cannot be used'))
    
        if len(val) < 2:
            raise Invalid(_('Name must be at least %s characters long') % 2)
        if len(val) > PACKAGE_NAME_MAX_LENGTH:
            raise Invalid(_('Name must be a maximum of %i characters long') % \
                          PACKAGE_NAME_MAX_LENGTH)
        if not name_match.match(val):
            raise Invalid(_('Username should be lowercase letters and/or numbers and/or these symbols: -_'))
        
        raise invalid
        

class RequestController(ckan.controllers.user.UserController):
    request_register_form = 'user/request_register.html'
    
    @staticmethod
    @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    def _validate_form(data, errors):
        ''' The functionality of sending emails with new user requests has been deprecated.
            Deprecated since 13.08.2014 - hdx 0.3.6 
        '''
        if not data['fullname']:
            errors['fullname'] = [_(u'Fullname is required!')]
        if not data['email']:
            errors['email'] = [_(u'Email is required!')]
        else:
            if not EMAIL_REGEX.match(data['email']):
                errors['email'] = [_(u'Email entered is not valid!')]

        if not data['org']:
            errors['org'] = [_(u'Organisation is required!')]

    @maintain.deprecated('The functionality of sending emails with new user requests has been deprecated')
    def request(self, data=None, errors=None, error_summary=None):
        ''' The functionality of sending emails with new user requests has been deprecated.
            Deprecated since hdx 0.3.5
        '''

        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'request': 'request' in request.params}
        #try:
        #    check_access('request_register', context)
        #except NotAuthorized:
        #    abort(401, _('Unauthorized to request new registration.'))

        if context['request'] and not data:
            data = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            errors = dict()
            error_summary = dict()

            self._validate_form(data, errors)
            try:
                captcha.check_recaptcha(request)
            except captcha.CaptchaError:
                error_msg = _(u'Bad Captcha. Please try again.')
                error_summary['captcha'] = error_msg
                errors['captcha'] = [error_msg]

            if errors == {}:
                name = data['fullname']
                email = data['email']
                org = data['org']
                reason = data['reason']

                h.log.info('Request access for {name} ({email}) of {org} with reason: {reason}'.format(name = name, email = email, org = org, reason=reason))
                try:
                    send_mail(name, email, org, reason)
                    h.flash_success(_('We will check your request and we will send you an email!'))
                    h.redirect_to('/')
                except mailer.MailerException, e:
                    error_summary['sendError'] = _('Could not send request for access: %s') % unicode(e)

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data,
                'errors': errors,
                'error_summary': error_summary,
                'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey')}
        c.form = render(self.request_register_form, extra_vars=vars)
        return base.render(self.request_register_form, cache_force=True, extra_vars=vars)


    def register(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session, 'user': c.user}
        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to register as a user.'))
        #hack to disable check if user is logged in
        save_user = c.user
        c.user = None
        result = self.new(data, errors, error_summary)
        c.user = save_user

        return result

    def post_register(self):
        if not c.user:
            user = request.params.get('user')
            vars = {'user':user}
            return render('user/post_register.html', extra_vars=vars)
        else:
            return render('user/logout_first.html')

    
    def new(self, data=None, errors=None, error_summary=None):
        '''GET to display a form for registering a new user.
           or POST the form data to actually do the user registration.
        '''
        
        temp_schema = self._new_form_to_db_schema()
        if temp_schema.has_key('name'):
           temp_schema['name'] = [name_validator_with_changed_msg if var==name_validator else var for var in temp_schema['name'] ]
        
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': temp_schema,
                   'save': 'save' in request.params}

        try:
            check_access('user_create', context)
        except NotAuthorized:
            abort(401, _('Unauthorized to create a user'))

        if context['save'] and not data:
            return self._save_new(context)

        if c.user and not data:
            # #1799 Don't offer the registration form if already logged in
            return render('user/logout_first.html')

        data = data or {}
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 
                'error_summary': error_summary,
                'capcha_api_key': configuration.config.get('ckan.recaptcha.publickey')}

        c.is_sysadmin = new_authz.is_sysadmin(c.user)
        c.form = render(self.new_user_form, extra_vars=vars)
        return render('user/new.html')

    def _save_new(self, context):
        try:
            data_dict = logic.clean_dict(unflatten(
                logic.tuplize_dict(logic.parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            captcha.check_recaptcha(request)
            user = get_action('user_create')(context, data_dict)
            token = get_action('token_create')(context, user)
        except NotAuthorized:
            abort(401, _('Unauthorized to create user %s') % '')
        except NotFound, e:
            abort(404, _('User not found'))
        except DataError:
            abort(400, _(u'Integrity Error'))
        except captcha.CaptchaError:
            error_msg = _(u'Bad Captcha. Please try again.')
            h.flash_error(error_msg)
            return self.new(data_dict)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)
        if not c.user:
            # Send validation email
            self.send_validation_email(user,token)

            # Redirect to a URL picked up by repoze.who which performs the
            # login
            #login_url = self._get_repoze_handler('login_handler_path')

            post_register_url = h.url_for(controller='ckanext.hdx_users.controllers.registration_controller:RequestController', action='post_register')

            # We need to pass the logged in URL as came_from parameter
            # otherwise we lose the language setting
            came_from = h.url_for(controller='user', action='logged_in',
                                  __ckan_no_root=True)
            redirect_url = '{0}?came_from={1}&user={2}'
            h.redirect_to(redirect_url.format(
                post_register_url,
                came_from, user['id']))
        else:
            # #1799 User has managed to register whilst logged in - warn user
            # they are not re-logged in as new user.
            h.flash_success(_('User "%s" is now registered but you are still '
                            'logged in as "%s" from before') %
                            (data_dict['name'], c.user))
            return render('user/logout_first.html')

    def validation_resend(self, id):
        #Get user by id
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj}

        try:
            user = get_action('user_show')(context, data_dict)
        except NotFound, e:
            abort(404, _('User not found'))
        except:
            abort(500, _('Error'))

        #Get token for user
        try:
            token = get_action('token_show')(context, data_dict)
        except NotFound, e:
            abort(404, _('User not found'))
        except:
            abort(500, _('Error'))

        #Send Validation email
        self.send_validation_email(user,token)

        post_register_url = h.url_for(controller='ckanext.hdx_users.controllers.registration_controller:RequestController', action='post_register')
        redirect_url = '{0}?user={1}'
        h.redirect_to(redirect_url.format(
                post_register_url,
                user['id']))



    def send_validation_email(self, user, token):
        validate_link = h.url_for(controller='ckanext.hdx_users.controllers.registration_controller:RequestController', action='validate',
                                  token=token['token'])
        link = '{0}{1}'
        body = 'Hello! Thank you for registering for an HDX account. '\
           'Please click the following link to validate your email\n' \
           '{link}\n' \
           ''.format(link=link.format(h.full_current_url(), validate_link))

        try:
            mailer.mail_recipient("HDX Registration", user['email'], "HDX: Validate Your Email", body)
            return True
        except:
            return False

    def validate(self, token):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'token': token,
                     'user_obj': c.userobj}
        #Update token for user
        try:
            token = get_action('token_update')(context, data_dict)
        except NotFound, e:
            abort(404, _('Token not found'))
        except:
            abort(500, _('Error'))

        #Set Flash message
        h.flash_success(_('Your email has been validated. You may now login.'))
        #Redirect to login
        h.redirect_to('login')

