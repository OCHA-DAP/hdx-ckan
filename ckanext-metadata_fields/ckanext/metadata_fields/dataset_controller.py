import logging
from urllib import urlencode
import datetime

from pylons import config
from genshi.template import MarkupTemplate
from genshi.template.text import NewTextTemplate
from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.maintain as maintain
import ckan.lib.package_saver as package_saver
import ckan.lib.i18n as i18n
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.accept as accept
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.datapreview as datapreview
import ckan.lib.plugins
import ckan.new_authz as new_authz


from ckan.common import OrderedDict, _, json, request, c, g, response
from home import CACHE_PARAMETERS

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
flatten_to_string_key = logic.flatten_to_string_key

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

from ckan.controllers.package import PackageController

class DatasetController(PackageController):

	def new(self, data=None, errors=None, error_summary=None):
		package_type = self._guess_package_type(True)

		context = {'model': model, 'session': model.Session,
				   'user': c.user or c.author,
				   'save': 'save' in request.params}

		# Package needs to have a organization group in the call to
		# check_access and also to save it
		try:
			check_access('package_create', context)
		except NotAuthorized:
			abort(401, _('Unauthorized to create a package'))

		if context['save'] and not data:
			return self._save_new(context, package_type=package_type)

		data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
			request.params, ignore_keys=CACHE_PARAMETERS))))
		c.resources_json = h.json.dumps(data.get('resources', []))
		# convert tags if not supplied in data
		if data and not data.get('tag_string'):
			data['tag_string'] = ', '.join(
				h.dict_list_reduce(data.get('tags', {}), 'name'))

		errors = errors or {}
		error_summary = error_summary or {}
		# in the phased add dataset we need to know that
		# we have already completed stage 1
		stage = ['active']
		if data.get('state') == 'draft':
			stage = ['active', 'complete']
		elif data.get('state') == 'draft-complete':
			stage = ['active', 'complete', 'complete']

		# if we are creating from a group then this allows the group to be
		# set automatically
		data['group_id'] = request.params.get('group') or \
			request.params.get('groups__0__id')

		vars = {'data': data, 'errors': errors,
				'error_summary': error_summary,
				'action': 'new', 'stage': stage}
		c.errors_json = h.json.dumps(errors)

		self._setup_template_variables(context, {},
									   package_type=package_type)

		# TODO: This check is to maintain backwards compatibility with the
		# old way of creating custom forms. This behaviour is now deprecated.
		if hasattr(self, 'package_form'):
			c.form = render(self.package_form, extra_vars=vars)
		else:
			c.form = render(self._package_form(package_type=package_type),
							extra_vars=vars)
		return render(self._new_template(package_type),
					  extra_vars={'stage': stage})



	def check_access(action, context, data_dict=None):
		user = context.get('user')

		log.debug('check access - user %r, action %s' % (user, action))

		if action:
		#if action != model.Action.READ and user in
		# (model.PSEUDO_USER__VISITOR, ''):
		#    # TODO Check the API key is valid at some point too!
		#    log.debug('Valid API key needed to make changes')
		#    raise NotAuthorized
			logic_authorization = new_authz.is_authorized(action, context, data_dict)
			if not logic_authorization['success']:
				msg = logic_authorization.get('msg', '')
				raise NotAuthorized(msg)
		elif not user:
			msg = _('No valid API key provided.')
			log.debug(msg)
			raise NotAuthorized(msg)

		log.debug('Access OK.')
		return True