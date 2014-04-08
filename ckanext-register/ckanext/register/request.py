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



class RequestController(ckan.controllers.user.UserController):

    def request(self):

        context = {'model': model, 'session': model.Session, 'user': c.user}
        data_dict = {'id': request.params.get('user')}
        #try:
        #    check_access('request_register', context)
        #except NotAuthorized:
        #    abort(401, _('Unauthorized to request new registration.'))

        if request.method == 'POST':
            email = request.params.get('email')
            h.log.info('Email is:'+email)

            if email:
                try:
                    #mailer.send_reset_link(user_obj)
                    h.flash_success(_('Please check your inbox for '
                                    'a reset code.'))
                    #h.redirect_to('/')
                except mailer.MailerException, e:
                    h.flash_error(_('Could not send reset link: %s') %
                                  unicode(e))

        return base.render('user/request_register.html', cache_force=True)