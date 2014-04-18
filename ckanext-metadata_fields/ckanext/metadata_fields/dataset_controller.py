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


	def new_resource(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']
            resource_id = data['id']
            del data['id']

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}

            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if value and key != 'resource_type':
                    data_provided = True
                    break

            if not data_provided and save_action != "go-dataset-complete":
                if save_action == 'go-dataset':
                    # go to final stage of adddataset
                    redirect(h.url_for(controller='package',
                                       action='edit', id=id))
                # see if we have added any resources
                try:
                    data_dict = get_action('package_show')(context, {'id': id})
                except NotAuthorized:
                    abort(401, _('Unauthorized to update dataset'))
                except NotFound:
                    abort(404,
                      _('The dataset {id} could not be found.').format(id=id))
                if not len(data_dict['resources']):
                    # no data so keep on page
                    msg = _('You must add at least one data resource')
                    # On new templates do not use flash message
                    if g.legacy_templates:
                        h.flash_error(msg)
                        redirect(h.url_for(controller='package',
                                           action='new_resource', id=id))
                    else:
                        errors = {}
                        error_summary = {_('Error'): msg}
                        return self.new_resource(id, data, errors, error_summary)
                # we have a resource so let them add metadata
                redirect(h.url_for(controller='package',
                                   action='new_metadata', id=id))

            data['package_id'] = id
            try:
                if resource_id:
                    data['id'] = resource_id
                    get_action('resource_update')(context, data)
                else:
                    get_action('resource_create')(context, data)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new_resource(id, data, errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to create a resource'))
            except NotFound:
                abort(404,
                    _('The dataset {id} could not be found.').format(id=id))
            if save_action == 'go-metadata':
                # go to final stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='new_metadata', id=id))
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        vars['pkg_name'] = id
        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        if pkg_dict['state'] == 'draft':
            vars['stage'] = ['complete', 'active']
        elif pkg_dict['state'] == 'draft-complete':
            vars['stage'] = ['complete', 'active', 'complete']
        return render('package/new_resource.html', extra_vars=vars)



    def new_metadata(self, id, data=None, errors=None, error_summary=None):
        ''' FIXME: This is a temporary action to allow styling of the
        forms. '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}

        if request.method == 'POST' and not data:
            save_action = request.params.get('save')
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']

            data_dict = get_action('package_show')(context, {'id': id})

            data_dict['id'] = id
            # update the state
            if save_action == 'finish':
                # we want this to go live when saved
                data_dict['state'] = 'active'
            elif save_action in ['go-resources', 'go-dataset']:
                data_dict['state'] = 'draft-complete'
            # allow the state to be changed
            context['allow_state_change'] = True
            data_dict.update(data)
            try:
                get_action('package_update')(context, data_dict)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new_metadata(id, data, errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to update dataset'))
            if save_action == 'go-resources':
                # we want to go back to the add resources form stage
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
            elif save_action == 'go-dataset':
                # we want to go back to the add dataset stage
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))

            redirect(h.url_for(controller='package', action='read', id=id))

        if not data:
            data = get_action('package_show')(context, {'id': id})
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        vars['pkg_name'] = id

        package_type = self._get_package_type(id)
        self._setup_template_variables(context, {},
                                       package_type=package_type)

        return render('package/new_package_metadata.html', extra_vars=vars)



