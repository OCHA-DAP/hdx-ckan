import ckan.controllers.user as ckan_user
import ckan.lib.helpers as h

from ckan.common import _, c, g, request
import ckan.logic as logic

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

			h.flash_success(_("%s is now logged in") %
							user_dict['display_name'])
			#return self.me()
			# Instead redirect to My orgs page
			return h.redirect_to(controller='user',
							  action='dashboard_organizations')
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