"""
Functions for creating and maintaining datasets.
"""
import logging
# from urllib import urlencode
#import datetime
import cgi
from string import lower
from ckanext.hdx_package.helpers.geopreview import GIS_FORMATS

from ckanext.hdx_package.helpers import helpers
#from ckanext.hdx_package.plugin import HDXPackagePlugin as hdx_package
#from formencode import foreach

from pylons import config
#from genshi.template.text import NewTextTemplate
#from paste.deploy.converters import asbool

import ckan.logic as logic
import ckan.lib.base as base
#import ckan.lib.maintain as maintain
#import ckan.lib.package_saver as package_saver
#import ckan.lib.i18n as i18n
import ckan.lib.navl.dictization_functions as dict_fns
#import ckan.lib.accept as accept
import ckan.lib.helpers as h
import ckan.model as model
import ckan.lib.datapreview as datapreview
import ckan.lib.plugins
import ckan.new_authz as new_authz
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.search as search

from ckan.common import _, json, request, c, g, response
from ckan.controllers.home import CACHE_PARAMETERS

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
DataError = ckan.lib.navl.dictization_functions.DataError
_check_group_auth = logic.auth.create._check_group_auth


CONTENT_TYPES = {
    'text': 'text/plain;charset=utf-8',
    'html': 'text/html;charset=utf-8',
    'json': 'application/json;charset=utf-8',
}


lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

from ckan.controllers.package import PackageController
#from ckan.controllers.api import ApiController

def clone_dict(old_dict):
    """
    Creates a copy of the data dictionary
    """
    data = dict()
    for k, v in old_dict.iteritems():
        data[k] = v
    return data


class DatasetController(PackageController):
    def _finish(self, status_int, response_data=None,
                content_type='text'):
        '''When a controller method has completed, call this method
        to prepare the response.
        @return response message - return this value from the controller
                                   method
                 e.g. return self._finish(404, 'Package not found')
        '''
        assert (isinstance(status_int, int))
        response.status_int = status_int
        response_msg = ''
        if response_data is not None:
            response.headers['Content-Type'] = CONTENT_TYPES[content_type]
            if content_type == 'json':
                response_msg = h.json.dumps(response_data)
            else:
                response_msg = response_data
            # Support "JSONP" callback.
            if status_int == 200 and 'callback' in request.params and \
                    (request.method == 'GET' or
                             c.logic_function and request.method == 'POST'):
                # escape callback to remove '<', '&', '>' chars
                callback = cgi.escape(request.params['callback'])
                response_msg = self._wrap_jsonp(callback, response_msg)
        return response_msg

    def _save_new(self, context, package_type=None):
        # The staged add dataset used the new functionality when the dataset is
        # partially created so we need to know if we actually are updating or
        # this is a real new.
        is_an_update = False
        ckan_phase = request.params.get('_ckan_phase')
        from ckan.lib.search import SearchIndexError

        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.POST))))
            if ckan_phase:
                # prevent clearing of groups etc
                context['allow_partial_update'] = True
                if 'tag_string' in data_dict:
                    # sort the tags
                    data_dict['tags'] = self._tag_string_to_list(data_dict['tag_string'])
                if data_dict.get('pkg_name'):
                    is_an_update = True
                    # This is actually an update not a save
                    data_dict['id'] = data_dict['pkg_name']
                    del data_dict['pkg_name']
                    #data_dict['state'] = 'draft'
                    # this is actually an edit not a save
                    pkg_dict = get_action('package_update')(context, data_dict)

                    if request.params['save'] == 'go-metadata':
                        # redirect to add metadata
                        url = h.url_for(controller='package',
                                        action='new_metadata',
                                        id=pkg_dict['name'])
                    else:
                        # redirect to add dataset resources
                        url = h.url_for(controller='package',
                                        action='new_resource',
                                        id=pkg_dict['name'])
                    redirect(url)
                # Make sure we don't index this dataset
                if request.params['save'] not in ['go-resource', 'go-metadata']:
                    data_dict['state'] = 'draft'
                # allow the state to be changed
                context['allow_state_change'] = True

            data_dict['type'] = package_type
            context['message'] = data_dict.get('log_message', '')
            pkg_dict = get_action('package_create')(context, data_dict)

            # A hack to handle the metadata correctly
            data_dict['id'] = pkg_dict['id']
            pkg_dict = get_action('package_update')(context, data_dict)

            if ckan_phase:
                # redirect to add dataset resources
                url = h.url_for(controller='package',
                                action='new_resource',
                                id=pkg_dict['name'])
                redirect(url)

            self._form_save_redirect(
                pkg_dict['name'], 'new', package_type=package_type)
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except NotFound, e:
            abort(404, _('Dataset not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            try:
                exc_str = unicode(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = unicode(str(e))
            abort(500, _(u'Unable to add package to search index.') + exc_str)
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            if is_an_update:
                # we need to get the state of the dataset to show the stage we
                # are on.
                pkg_dict = get_action('package_show')(context, data_dict)
                data_dict['state'] = pkg_dict['state']
                return self.edit(data_dict['id'], data_dict,
                                 errors, error_summary)
            data_dict['state'] = 'none'
            return self.new(data_dict, errors, error_summary)

    def preselect(self):
        """
        Force user to pick an organization before creating a dataset
        """
        #If user not logged in, redirect
        if not c.user:
            return redirect(h.url_for(controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='contribute'))

        c.am_sysadmin = new_authz.is_sysadmin(c.user)
        c.organizations_available = helpers.hdx_organizations_available_with_roles()
        if c.organizations_available and len(c.organizations_available) > 0:
            return base.render('organization/organization_preselector.html')
        else:
            return base.render('organization/request_mem_or_org.html')

    def new(self, data=None, errors=None, error_summary=None):
        """
        Creates a new dataset, modified to create two page flow
        (no longer needed) and to force users to join an org 
        (still needed)
        """
        # Is the user a member of any orgs? If not make them join one first
        try:
            user_orgs = helpers.hdx_user_org_num(c.userobj.id)
            if len(user_orgs) == 0:
                return render('organization/request_mem_or_org.html')
                # If there's an org and the user is not a member of this org
                # redirect back to org select
                this_org = request.params['organization_id']
                if this_org in user_orgs:
                    return render('organization/request_mem_or_org.html')
        except:
            return redirect(h.url_for(controller='ckanext.hdx_users.controllers.login_controller:LoginController', action='contribute'))

        package_type = self._guess_package_type(True)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
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
        if data.get('state', '').startswith('draft'):
            stage = ['active', 'complete']

        # if we are creating from a group then this allows the group to be
        # set automatically
        data['group_id'] = request.params.get('group') or \
                           request.params.get('groups__0__id')
        form_snippet = self._package_form(package_type=package_type)
        form_vars = {'data': data, 'errors': errors,
                     'error_summary': error_summary,
                     'action': 'new', 'stage': stage,
                     'dataset_type': package_type,
                    }
        c.errors_json = h.json.dumps(errors)

        self._setup_template_variables(context, {},
                                       package_type=package_type)

        new_template = self._new_template(package_type)
        c.form = ckan.lib.render.deprecated_lazy_render(
            new_template,
            form_snippet,
            lambda: render(form_snippet, extra_vars=form_vars),
            'use of c.form is deprecated. please see '
            'ckan/templates/package/base_form_page.html for an example '
            'of the new way to include the form snippet'
            )
        return render(new_template,
                      extra_vars={'form_vars': form_vars,
                                  'form_snippet': form_snippet,
                                  'dataset_type': package_type})
        #if not request.is_xhr:
        #    return render(self._new_template(package_type), extra_vars={'stage': stage, 'data': data})
        #else:
        #    return self._finish(200, {'validation_fail': 1, 'errors': vars['errors'],
        #                              'error_summary': vars['error_summary']}, content_type='json')
            # return render(self._new_template(package_type), extra_vars={'stage':
            # stage})

    # def _get_perma_link(self, dataset_id, resource_id):
    #     """
    #     Get perma link for resource
    #     """
    #     perma_link = h.url_for(
    #         'perma_storage_file', id=dataset_id, resource_id=resource_id)
    #     if '://' not in perma_link:
    #         perma_link = config.get(
    #             'ckan.site_url', '') + perma_link
    #     return perma_link

    def _update_or_create_resource(self, context, data, dataset_id, resource_id):
        gis_data = {"dataset_id": dataset_id, "resource_id": resource_id}
        if resource_id:
            get_action('resource_update')(context, data)

        else:
            get_action('resource_create')(context, data)

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
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            # see if we have any data that we are trying to save
            data_provided = False
            for key, value in data.iteritems():
                if ((value or isinstance(value, cgi.FieldStorage)) and key != 'resource_type'):
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
            # if 'format' in data and data['format'] == ZIPPED_SHAPEFILE_FORMAT:
            #     data['shape'] = self._get_geojson(data['url'])
            try:
                self._update_or_create_resource(context, data, id, resource_id)

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
                data_dict = get_action('package_show')(context, {'id': id})
                get_action('package_update')(
                    dict(context, allow_state_change=True),
                    dict(data_dict, state='active'))
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            elif save_action == 'go-dataset':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            ### Leaving this in HDX unless we update the templates
            elif save_action == 'finish':
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
            else:
                # add more resources
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'action': 'new', 'pkg_name': id}
        # get resources for sidebar
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            pkg_dict = get_action('package_show')(context, {'id': id})
        except NotFound:
            abort(404, _('The dataset {id} could not be found.').format(id=id))
        try:
            check_access(
                'resource_create', context, {"package_id": pkg_dict["id"]})
        except NotAuthorized:
            abort(401, _('Unauthorized to create a resource for this package'))

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type': package_type}
        vars['pkg_name'] = id
        # required for nav menu
        vars['pkg_dict'] = pkg_dict
        template = 'package/new_resource.html'
        if pkg_dict['state'].startswith('draft'):
            vars['stage'] = ['complete', 'active']
            template = 'package/new_resource.html'
        return render(template, extra_vars=vars)

        # # required for nav menu
        # vars['pkg_dict'] = pkg_dict
        # if pkg_dict['state'] == 'draft':
        #     vars['stage'] = ['complete', 'active']
        # elif pkg_dict['state'] == 'draft-complete':
        #     vars['stage'] = ['complete', 'active', 'complete']

        # if not request.is_xhr:
        #     return render('package/new_resource.html', extra_vars=vars)
        # else:
        #     # Adding url for easy update
        #     vars['action_url'] = h.url_for(
        #         controller='package', action='new_resource', id=vars['pkg_name'])
        #     return self._finish(200, vars, content_type='json')

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
            if save_action == 'finish' or save_action == 'finish-ajax':
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
            if save_action == 'go-resources' or 'finish-ajax':
                # we want to go back to the add resources form stage
                redirect(h.url_for(controller='package',
                                   action='new_resource', id=id))
            elif save_action == 'go-dataset':
                # we want to go back to the add dataset stage
                redirect(h.url_for(controller='package',
                                   action='edit', id=id))
            elif save_action == 'go-dataset-complete':
                # go to first stage of add dataset
                redirect(h.url_for(controller='package',
                                   action='read', id=id))
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

        if not request.is_xhr:
            return render('package/new_package_metadata.html', extra_vars=vars)
        else:
            vars['action_url'] = h.url_for(
                controller='package', action='new_metadata', id=vars['pkg_name'])
            return self._finish(200, vars, content_type='json')

    def resource_edit(self, id, resource_id, data=None, errors=None,
                      error_summary=None):
        """
        Edit resource metadata
        """
        if request.method == 'POST' and not data:
            data = data or clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(
                request.POST))))
            # we don't want to include save as it is part of the form
            del data['save']

            context = {'model': model, 'session': model.Session,
                       'api_version': 3, 'for_edit': True,
                       'user': c.user or c.author, 'auth_user_obj': c.userobj}

            data['package_id'] = id
            try:
                self._update_or_create_resource(context, data, id, resource_id)
            except ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.resource_edit(id, resource_id, data,
                                          errors, error_summary)
            except NotAuthorized:
                abort(401, _('Unauthorized to edit this resource'))
            redirect(h.url_for(controller='package', action='resources',
                               id=id, resource_id=resource_id))

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True, 'use_cache': False,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            check_access('resource_update', context, {'id': resource_id})
        except NotAuthorized:
            abort(401, _('Unauthorized to edit this resource'))
        pkg_dict = get_action('package_show')(context, {'id': id})
        if pkg_dict['state'].startswith('draft'):
            # dataset has not yet been fully created
            resource_dict = get_action('resource_show')(
                context, {'id': resource_id})
            fields = [
                'url', 'resource_type', 'format', 'name', 'description', 'id']
            data = {}
            for field in fields:
                data[field] = resource_dict[field]
            return self.new_resource(id, data=data)
        # resource is fully created
        try:
            resource_dict = get_action('resource_show')(
                context, {'id': resource_id})
        except NotFound:
            abort(404, _('Resource not found'))
        c.pkg_dict = pkg_dict
        c.resource = resource_dict
        # set the form action
        c.form_action = h.url_for(controller='package',
                                  action='resource_edit',
                                  resource_id=resource_id,
                                  id=id)
        if not data:
            data = resource_dict

        package_type = pkg_dict['type'] or 'dataset'

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new',
                'resource_form_snippet': self._resource_form(package_type),
                'dataset_type':package_type}
        return render('package/resource_edit.html', extra_vars=vars)

    def _create_perma_link_if_needed(self, dataset_id, resource):
        """
        Create a perma link
        """
        if 'perma_link' not in resource and resource.get('resource_type', '') == 'file.upload':
            domain = config.get('ckan.site_url', '')
            if domain and domain in resource.get('url', ''):
                perma_link = h.url_for(
                    'perma_storage_file', id=dataset_id, resource_id=resource['id'])
                resource['perma_link'] = domain + perma_link

    def read(self, id, format='html'):
        """
        Display the package, includes HDX additions for continuous browsing
        """
        if not format == 'html':
            ctype, extension = \
                self._content_type_from_extension(format)
            if not ctype:
                # An unknown format, we'll carry on in case it is a
                # revision specifier and re-constitute the original id
                id = "%s.%s" % (id, format)
                ctype, format = "text/html; charset=utf-8", "html"
        else:
            ctype, format = self._content_type_from_accept()

        response.headers['Content-Type'] = ctype

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        data_dict = {'id': id}

        # interpret @<revision_id> or @<date> suffix
        split = id.split('@')
        if len(split) == 2:
            data_dict['id'], revision_ref = split
            if model.is_id(revision_ref):
                context['revision_id'] = revision_ref
            else:
                try:
                    date = h.date_str_to_datetime(revision_ref)
                    context['revision_date'] = date
                except TypeError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
                except ValueError, e:
                    abort(400, _('Invalid revision format: %r') % e.args)
        elif len(split) > 2:
            abort(400, _('Invalid revision format: %r') %
                  'Too many "@" symbols')

        # check if package exists
        try:
            c.pkg_dict = get_action('package_show')(context, data_dict)
            c.pkg = context['package']
        except NotFound:
            abort(404, _('Dataset not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % id)

        # used by disqus plugin
        c.current_package_id = c.pkg.id
        c.related_count = c.pkg.related_count

        for resource in c.pkg_dict['resources']:
            # create permalink if needed
            #self._create_perma_link_if_needed(id, resource)

            # can the resources be previewed?
            resource['can_be_previewed'] = self._resource_preview(
                {'resource': resource, 'package': c.pkg_dict})

            resource_views = get_action('resource_view_list')(
                context, {'id': resource['id']})
            resource['has_views'] = len(resource_views) > 0

        # Is this an indicator? Load up graph data
        #c.pkg_dict['indicator'] = 1
        try:
            if int(c.pkg_dict['indicator']):
                c.pkg_dict['graph'] = '{}'
                c.pkg_dict['indicator'] = 1
            else:
                c.pkg_dict['indicator'] = 0
        except:
            # If there's no indicator value it isn't an indicator
            c.pkg_dict['indicator'] = 0

        package_type = c.pkg_dict['type'] or 'dataset'
        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        #package_saver.PackageSaver().render_package(c.pkg_dict, context)

        template = self._read_template(package_type)
        template = template[:template.index('.') + 1] + format

        # changes done for indicator
        act_data_dict = {'id': c.pkg_dict['id'], 'limit': 7}
        c.hdx_activities = get_action(
            'hdx_get_activity_list')(context, act_data_dict)
        c.related_count = c.pkg.related_count

        # count the number of resource downloads
        c.downloads_count = 0
        for resource in c.pkg_dict['resources']:
            if resource['tracking_summary']:
                c.downloads_count += resource['tracking_summary']['total']

        followers = get_action('dataset_follower_list')({'ignore_auth': True},
                                                        {'id': c.pkg_dict['id']})
        if followers and len(followers) > 0:
            c.followers = [{'url': h.url_for(controller='user',
                                             action='read', id=f['name']), 'name': f['fullname'] or f['name']}
                           for f in followers]
        # topics
        topics_obj = helpers.pkg_topics_list({'id': c.pkg_dict['id']})
        topics = model_dictize.tag_list_dictize(topics_obj, context)

        if topics and len(topics) > 0:
            c.topics = [
                {'url': h.url_for(controller='package', action='search', vocab_Topics=t['name']), 'name': t['name']}
                for t in topics]
        # related websites
        c.related_urls = [{'url': 'http://reliefweb.int', 'name': 'ReliefWeb'}, {
            'url': 'http://www.unocha.org', 'name': 'UNOCHA'},
                          {'url': 'http://www.humanitarianresponse.info', 'name': 'HumanitarianResponse'},
                          {'url': 'http://fts.unocha.org', 'name': 'OCHA Financial Tracking Service'}]

        has_shapes = False
        if 'resources' in c.pkg_dict:
            has_shapes = self._has_shapes(c.pkg_dict['resources'])
        try:
            if has_shapes:
                c.shapes = json.dumps(self._process_shapes(c.pkg_dict['resources']))
                return render('indicator/hdx-shape-read.html')
            if int(c.pkg_dict['indicator']):
                return render('indicator/read.html')
            else:
                org_dict = c.pkg_dict.get('organization') or {}
                org_id = org_dict.get('id', None)
                org_info_dict = self._get_org_extras(org_id)
                if org_info_dict.get('custom_org', False):
                    self._process_customizations(org_info_dict.get('customization', None))
                    return render('package/custom_hdx_read.html')
                return render('package/hdx_read.html')
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(
                package_type=package_type, format=format, file=template))
            abort(404, msg)

        assert False, "We should never get here"

    def _get_org_extras(self, org_id):
        """
        Get the extras for our orgs
        """
        if not org_id:
            return {}
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'include_datasets': False,
                   'for_view': True}
        data_dict = {'id': org_id}
        org_info = get_action(
                'hdx_light_group_show')(context, data_dict)

        extras_dict = {item['key']: item['value'] for item in org_info.get('extras',{})}
        extras_dict['image_url'] = org_info.get('image_url', None)

        return extras_dict

    def _process_customizations(self, json_string):
        """
        Process settings for datasets belonging to custom layouts 
        """
        c.logo_config = {
          'background_color': '#fafafa',
          'border_color': '#cccccc'
        }
        if json_string:
            custom_dict = json.loads(json_string)
            image_name = custom_dict.get('image_rect', None)
            if image_name:
                c.logo_config['image_url'] = h.url_for('image_serve', label=image_name)

            if 'true' == custom_dict.get('use_org_color', False):
                c.logo_config['background_color'] = custom_dict.get('highlight_color', '#fafafa')
                c.logo_config['border_color'] = custom_dict.get('highlight_color', '#cccccc')

    def _has_shapes(self, resources):
        for resource in resources:
            if self._has_shape_info(resource):
                return True
        return False

    def _has_shape_info(self, resource):
        if lower(resource.get('format', '')) in GIS_FORMATS and resource.get('shape_info'):
            shp_info = json.loads(resource['shape_info'])
            if shp_info.get('state', '') == 'success':
                return True
        return False

    def _process_shapes(self, resources):
        result = {}
        context = {'model': model, 'session': model.Session,
           'user': c.user or c.author, 'auth_user_obj': c.userobj}

        for resource in resources:
            if self._has_shape_info(resource):
                res_pbf_template_url = config.get('hdx.gis.resource_pbf_url')
                shp_info = json.loads(resource['shape_info'])

                res_pbf_url = res_pbf_template_url.replace('{resource_id}', shp_info['layer_id'])
                name = resource['name']
                result[name] = {
                    'url': res_pbf_url,
                    'bounding_box': shp_info['bounding_box'],
                    'layer_fields': shp_info.get('layer_fields', [])
                }
        return result

    # @staticmethod
    # def _get_json_from_resource(resource):
    #     """
    #     Get json from the resource files
    #     """
    #     if not resource:
    #         return None
    #     urls_dict = {'url': resource}
    #     g_json = get_action('hdx_get_json_from_resource')({}, urls_dict)
    #     return g_json
    # 
    # @staticmethod
    # def _get_geojson(url):
    #     """
    #     Get geojson from resources
    #     """
    #     ogre_url = config.get('hdx.ogre.url')
    #     urls_dict = {'shape_source_url': url, 'convert_url': ogre_url+'/convert'}
    #     g_json = get_action('hdx_get_shape_geojson')({}, urls_dict)
    #     return g_json
    #
    # def _get_shape_info_as_json(self, gis_data):
    #     resource_id = gis_data['resource_id']
    #     resource_id = resource_id if resource_id and resource_id.strip() else 'new'
    #
    #     layer_import_url = config.get('hdx.gis.layer_import_url')
    #     gis_url = layer_import_url.replace("{dataset_id}", gis_data['dataset_id']).replace("{resource_id}",
    #                 resource_id).replace("{resource_download_url}", gis_data['url'])
    #     result = get_action('hdx_get_shape_info')({}, {"gis_url": gis_url})
    #     return result

    def _resource_preview(self, data_dict):
        """
        Preview resources
        """
        if 'format' not in data_dict['resource'] or not data_dict['resource']['format']:
            return False
        '''Deprecated in 2.3'''
        return bool(datapreview.get_preview_plugin(data_dict, return_first=True))

    def shorten(self):
        """
        Use Google's url shorten to create social sharing links
        """
        import requests

        params = request.params.items()
        url = params[0][1]
        r = requests.post("https://www.googleapis.com/urlshortener/v1/url",
                          data=json.dumps({'longUrl': url}), headers={'content-type': 'application/json'})
        item = r.json()

        try:
            short = item['id']
        except Exception as e:
            log.warning('There was a problem shortening url {}. Shortener response: {}'.format(url, r.text))
            short = url
        return self._finish(200, {'url': short}, content_type='json')

    def visibility(self, id):
        """
        Toggle the visibility of the dataset
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        try:
            c.pkg_dict = get_action('package_show')(context, {'id': id})

        except NotAuthorized:
            return self._finish(401, {'success': False, 'message': 'Not authorized to do this.'}, content_type='json')
        except NotFound:
            return self._finish(404, {'success': False, 'message': 'No such dataset found.'}, content_type='json')

        if c.pkg_dict['private']:
            if c.pkg_dict['organization'] is None:
                return self._finish(200, {'success': False,
                                          'message': 'Datasets that do not belong to an organization cannot be private.'},
                                    content_type='json')
            text = 'make it private'
            status = 'Public'
            data_dict = c.pkg_dict
            data_dict['private'] = False
        else:
            text = 'make it public'
            status = 'Private'
            data_dict = c.pkg_dict
            data_dict['private'] = True
        if data_dict.get('extras', None):
            del(data_dict['extras'])
        if not data_dict.get('dataset_source', None):
            data_dict['dataset_source'] = "Unknown"
        if not data_dict.get('package_creator', None):
            data_dict['package_creator'] = "Unknown"

        try:
            pkg_dict = get_action('package_update')(context, data_dict)
        except:
            self._finish(500, {'success': False, 'message':"Oops! We can't do this right now. Something went wrong."}, content_type='json') 
        return self._finish(200, {'success': True, 'status': status, 'text': text}, content_type='json')


    # copy from package.py:1094
    def resource_delete(self, id, resource_id):
        """
        Delete a resource, HDX changed the redirection point.
        """

        if 'cancel' in request.params:
            h.redirect_to(
                controller='package', action='resource_edit', resource_id=resource_id, id=id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            check_access('package_delete', context, {'id': id})
        except NotAuthorized:
            abort(401, _('Unauthorized to delete package %s') % '')

        try:
            if request.method == 'POST':
                get_action('resource_delete')(context, {'id': resource_id})
                h.flash_notice(_('Resource has been deleted.'))
                h.redirect_to(controller='package', action='resources',
                              id=id)
            c.resource_dict = get_action('resource_show')(
                context, {'id': resource_id})
            c.pkg_id = id
        except NotAuthorized:
            abort(401, _('Unauthorized to delete resource %s') % '')
        except NotFound:
            abort(404, _('Resource not found'))
        return render('package/confirm_delete_resource.html', {'dataset_type': self._get_package_type(id)})

    def resource_download(self, id, resource_id):
        '''
        This is a wrapper of the core ckan function.
        It's meant to allow old style HDX perma_links (/dataset/{id}/resource_download/{resource_id})
        to still function for ppl that have bookmarked the url or for custom pages.

        :param id: package id
        :type id: string
        :param resource_id: resource id
        :type resource_id: string
        :return:
        :rtype:
        '''
        result = super(DatasetController, self).resource_download(id, resource_id)
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            rsc = get_action('resource_show')(context, {'id': resource_id})
            response.headers['Content-Disposition'] = 'inline; filename="{}"'.format(rsc.get('name', 'download'))
        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read resource %s') % id)

        return result

    def delete(self, id):
        """
        Delete package, HDX changed the redirection point
        """
        if 'cancel' in request.params:
            h.redirect_to(controller='package', action='edit', id=id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            check_access('package_delete', context, {'id': id})
        except NotAuthorized:
            abort(401, _('Unauthorized to delete package %s') % '')

        try:
            if request.method == 'POST':
                get_action('package_purge')(context, {'id': id}) #Create new action to fully delete
                h.flash_notice(_('Dataset has been deleted.'))
                h.redirect_to(controller='user', action='dashboard_datasets')
            c.pkg_dict = get_action('package_show')(context, {'id': id})
            dataset_type = c.pkg_dict['type'] or 'dataset'
        except NotAuthorized:
            abort(401, _('Unauthorized to delete package %s') % '')
        except NotFound:
            abort(404, _('Dataset not found'))
        return render('package/confirm_delete.html',
                      extra_vars={'dataset_type': dataset_type})

#copy from package.py:1183
#related to issue 2367
    def resource_read(self, id, resource_id):
        """
        Display resource, modified to add permalinks
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}

        try:
            c.resource = get_action('resource_show')(context,
                                                     {'id': resource_id})
            c.package = get_action('package_show')(context, {'id': id})
            # required for nav menu
            c.pkg = context['package']
            c.pkg_dict = c.package
            #self._create_perma_link_if_needed(id, c.resource)
        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read resource %s') % id)
        # get package license info
        license_id = c.package.get('license_id')
        try:
            c.package['isopen'] = model.Package.\
                get_license_register()[license_id].isopen()
        except KeyError:
            c.package['isopen'] = False

        dataset_type = c.pkg_dict['type'] or 'dataset'

        # TODO: find a nicer way of doing this
        c.datastore_api = '%s/api/action' % config.get(
            'ckan.site_url', '').rstrip('/')

        c.related_count = c.pkg.related_count

        c.resource['can_be_previewed'] = self._resource_preview(
            {'resource': c.resource, 'package': c.package})

        resource_views = get_action('resource_view_list')(
            context, {'id': resource_id})
        c.resource['has_views'] = len(resource_views) > 0

        current_resource_view = None
        view_id = request.GET.get('view_id')
        if c.resource['can_be_previewed'] and not view_id:
            current_resource_view = None
        elif c.resource['has_views']:
            if view_id:
                current_resource_view = [rv for rv in resource_views
                                         if rv['id'] == view_id]
                if len(current_resource_view) == 1:
                    current_resource_view = current_resource_view[0]
                else:
                    abort(404, _('Resource view not found'))
            else:
                current_resource_view = resource_views[0]

        vars = {'resource_views': resource_views,
                'current_resource_view': current_resource_view,
                'dataset_type': dataset_type}

        template = self._resource_template(dataset_type)
        return render(template, extra_vars=vars)


    def resource_datapreview(self, id, resource_id):
        '''
        Modified by HDX - from package controller.
        - change to have protocol-relative URL

        Embeded page for a resource data-preview.

        Depending on the type, different previews are loaded.  This could be an
        img tag where the image is loaded directly or an iframe that embeds a
        webpage, recline or a pdf preview.
        '''
        context = {
            'model': model,
            'session': model.Session,
            'user': c.user or c.author,
            'auth_user_obj': c.userobj
        }

        try:
            c.resource = get_action('resource_show')(context,
                                                     {'id': resource_id})
            c.package = get_action('package_show')(context, {'id': id})

            data_dict = {'resource': c.resource, 'package': c.package}

            preview_plugin = datapreview.get_preview_plugin(data_dict)

            if preview_plugin is None:
                abort(409, _('No preview has been defined.'))

            preview_plugin.setup_template_variables(context, data_dict)

            # If the browser is going to make a direct request (not via dataproxy) for
            # the resource it needs to have protocol-relative url
            if preview_plugin and preview_plugin.name == 'text_preview':
                c.resource['url'] = c.resource['url'].replace('http://', '//').replace(':5000', '')

            c.resource_json = json.dumps(c.resource)
        except NotFound:
            abort(404, _('Resource not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read resource %s') % id)
        else:
            return render(preview_plugin.preview_template(context, data_dict))

