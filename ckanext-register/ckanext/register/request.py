import ckan.lib.base as base
import ckan.controllers.user
from ckan.common import _, c, request
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.model as model
import ckan.logic as logic

abort = base.abort
check_access = logic.check_access
get_action = logic.get_action

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized

def send_mail(name, email, org, reason = ''):
    body = 'New user registration request\n' \
           'Full Name: {fn}\n' \
           'Email: {mail}\n' \
           'Organisation: {org}\n' \
           'Reason: {reason}\n' \
           '(This is an automated mail)' \
           ''.format(fn=name, mail=email, org=org, reason=reason)

    mailer.mail_recipient("Registration", "test@test.com", "New user registration", body)

    return

class RequestController(ckan.controllers.user.UserController):

    def request(self):

        context = {'model': model, 'session': model.Session, 'user': c.user}
        data_dict = {'id': request.params.get('user')}
        #try:
        #    check_access('request_register', context)
        #except NotAuthorized:
        #    abort(401, _('Unauthorized to request new registration.'))

        if request.method == 'POST':
            name = request.params.get('fullname')
            email = request.params.get('email')
            org = request.params.get('org')
            reason = request.params.get('reason')

            h.log.info('Request access for {name} ({email}) of {org} with reason: {reason}'.format(name = name, email = email, org = org, reason=reason))

            if name and email and org:
                try:
                    send_mail(name, email, org, reason)
                    h.flash_success(_('Please check your inbox for '
                                    'a reset code.'))
                    #h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(_('Could not send reset link: %s') %
                                  unicode(e))
            else:
                h.flash_error(_('Please fill all the fields!'))
                return

        return base.render('user/request_register.html', cache_force=True)