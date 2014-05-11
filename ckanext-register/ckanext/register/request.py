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

from ckan.logic.validators import name_validator, name_match, PACKAGE_NAME_MAX_LENGTH


EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
abort = base.abort
check_access = logic.check_access
render = base.render
NotAuthorized = logic.NotAuthorized
unflatten = dictization_functions.unflatten
ValidationError = logic.ValidationError

Invalid = df.Invalid


def send_mail(name, email, org, reason = ''):
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
    def _validate_form(data, errors):
        if not data['fullname']:
            errors['fullname'] = [_(u'Fullname is required!')]
        if not data['email']:
            errors['email'] = [_(u'Email is required!')]
        else:
            if not EMAIL_REGEX.match(data['email']):
                errors['email'] = [_(u'Email entered is not valid!')]

        if not data['org']:
            errors['org'] = [_(u'Organisation is required!')]

    def request(self, data=None, errors=None, error_summary=None):

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
