import logging
from urllib import urlencode
import datetime
import cgi

from ckanext.hdx_package.helpers import helpers
#import ckanext.hdx_package.plugin.HDXPackagePlugin as hdx_package
from ckanext.hdx_package.plugin import HDXPackagePlugin as hdx_package

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
import ckan.lib.dictization.model_dictize as model_dictize

from ckan.common import OrderedDict, _, json, request, c, g, response
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

CONTENT_TYPES = {
    'text': 'text/plain;charset=utf-8',
    'html': 'text/html;charset=utf-8',
    'json': 'application/json;charset=utf-8',
}

lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin

from ckan.controllers.package import PackageController


class DatasetController(PackageController):

    def _finish(self, status_int, response_data=None,
                content_type='text'):
        '''When a controller method has completed, call this method
        to prepare the response.
        @return response message - return this value from the controller
                                   method
                 e.g. return self._finish(404, 'Package not found')
        '''
        assert(isinstance(status_int, int))
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
                # sort the tags
                data_dict['tags'] = self._tag_string_to_list(
                    data_dict['tag_string'])
                if data_dict.get('pkg_name'):
                    is_an_update = True
                    # This is actually an update not a save
                    data_dict['id'] = data_dict['pkg_name']
                    del data_dict['pkg_name']
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
        c.am_sysadmin = new_authz.is_sysadmin(c.user)
        c.organizations_available = helpers.hdx_organizations_available_with_roles()
        if c.organizations_available and len(c.organizations_available) > 0:
            return base.render('organization/organization_preselector.html')
        else:
            return base.render('organization/request_mem_or_org.html')

    def new(self, data=None, errors=None, error_summary=None):
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
            return render('user/login.html', extra_vars={'contribute': True})

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
        stage = ['inactive']
        if data.get('state') == 'draft':
            stage = ['inactive', 'complete']
        elif data.get('state') == 'draft-complete':
            stage = ['inactive', 'complete', 'complete']

        # if we are creating from a group then this allows the group to be
        # set automatically
        data['group_id'] = request.params.get('group') or \
            request.params.get('groups__0__id')

        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary,
                'action': 'new', 'stage': stage, 'validation_fail': 0}
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

        if not request.is_xhr:
            return render(self._new_template(package_type), extra_vars={'stage': stage, 'data': data})
        else:
            return self._finish(200, {'validation_fail': 1, 'errors': vars['errors'], 'error_summary': vars['error_summary']}, content_type='json')
        # return render(self._new_template(package_type), extra_vars={'stage':
        # stage})

    def _get_perma_link(self, dataset_id, resource_id):
        perma_link = h.url_for(
            'perma_storage_file', id=dataset_id, resource_id=resource_id)
        if '://' not in perma_link:
            perma_link = config.get(
                'ckan.site_url', '') + perma_link
        return perma_link

    def _update_or_create_resource(self, context, data, dataset_id, resource_id):
        if resource_id:
            data['id'] = resource_id
            # Added by HDX - adding perma_link
            if 'resource_type' in data and u'file.upload' == data['resource_type']:
                data['perma_link'] = self._get_perma_link(
                    dataset_id, resource_id)

            get_action('resource_update')(context, data)
        else:
            result_dict = get_action('resource_create')(context, data)

            # Added by HDX - adding perma_link
            # Now that we have a resource id we want to add the
            # perma_link url to the resource
            if 'resource_type' in result_dict and u'file.upload' == result_dict['resource_type']:
                result_dict['perma_link'] = self._get_perma_link(
                    dataset_id, result_dict['id'])
                get_action('resource_update')(context, result_dict)

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
            elif save_action == 'finish':
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

        if not request.is_xhr:
            return render('package/new_resource.html', extra_vars=vars)
        else:
            # Adding url for easy update
            vars['action_url'] = h.url_for(
                controller='package', action='new_resource', id=vars['pkg_name'])
            return self._finish(200, vars, content_type='json')

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
                               id=id))

        context = {'model': model, 'session': model.Session,
                   'api_version': 3, 'for_edit': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj}
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

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        return render('package/resource_edit.html', extra_vars=vars)

    def _create_perma_link_if_needed(self, dataset_id, resource):
        if 'perma_link' not in resource and resource.get('resource_type', '') == 'file.upload':
            domain = config.get('ckan.site_url', '')
            if domain and domain in resource.get('url', ''):
                perma_link = h.url_for(
                    'perma_storage_file', id=dataset_id, resource_id=resource['id'])
                resource['perma_link'] = perma_link

    def read(self, id, format='html'):
        if not format == 'html':
            ctype, extension, loader = \
                self._content_type_from_extension(format)
            if not ctype:
                # An unknown format, we'll carry on in case it is a
                # revision specifier and re-constitute the original id
                id = "%s.%s" % (id, format)
                ctype, format, loader = "text/html; charset=utf-8", "html", \
                    MarkupTemplate
        else:
            ctype, format, loader = self._content_type_from_accept()

        response.headers['Content-Type'] = ctype

        package_type = self._get_package_type(id.split('@')[0])
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
            self._create_perma_link_if_needed(id, resource)

            # can the resources be previewed?
            resource['can_be_previewed'] = self._resource_preview(
                {'resource': resource, 'package': c.pkg_dict})
        print c.pkg.related

        # Is this an indicator? Load up graph data
        #c.pkg_dict['indicator'] = 1
        try:
            if int(c.pkg_dict['indicator']):
                c.pkg_dict['graph'] = '{}'
        except:
            # If there's no indicator value it isn't an indicator
            c.pkg_dict['indicator'] = 0

        self._setup_template_variables(context, {'id': id},
                                       package_type=package_type)

        package_saver.PackageSaver().render_package(c.pkg_dict, context)

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
                                             action='read', id=f['name']), 'name':f['fullname'] or f['name']}
                           for f in followers]
        # topics
        topics_obj = helpers.pkg_topics_list({'id': c.pkg_dict['id']})
        topics = model_dictize.tag_list_dictize(topics_obj, context)

        if topics and len(topics) > 0:
            c.topics = [{'url': h.url_for(controller='package', action='search', vocab_Topics=t['name']), 'name':t['name']}
                        for t in topics]
        # related websites
        c.related_urls = [{'url': 'http://reliefweb.int', 'name': 'ReliefWeb'}, {
            'url': 'http://www.unocha.org', 'name': 'UNOCHA'}, {'url': 'http://www.humanitarianresponse.info', 'name': 'HumanitarianResponse'}, {'url': 'http://fts.unocha.org', 'name': 'OCHA Financial Tracking Service'}]
        try:
            if int(c.pkg_dict['indicator']):
                return render('indicator/read.html', loader_class=loader)
            else:
                return render('package/hdx_read.html', loader_class=loader)
        except ckan.lib.render.TemplateNotFound:
            msg = _("Viewing {package_type} datasets in {format} format is "
                    "not supported (template file {file} not found).".format(
                        package_type=package_type, format=format, file=template))
            abort(404, msg)

        assert False, "We should never get here"

    def _resource_preview(self, data_dict):
        if 'format' not in data_dict['resource'] or not data_dict['resource']['format']:
            return False
        return bool(datapreview.res_format(data_dict['resource'])
                    in datapreview.direct() + datapreview.loadable()
                    or datapreview.get_preview_plugin(
                        data_dict, return_first=True))

    def shorten(self):
        import requests
        params = request.params.items()
        url = params[0][1]
        r = requests.post("https://www.googleapis.com/urlshortener/v1/url",
                          data=json.dumps({'longUrl': url}), headers={'content-type': 'application/json'})
        item = r.json()

        try:
            short = item['id']
        except:
            short = url
        return self._finish(200, {'url': short}, content_type='json')


# copy from package.py:1094
    def resource_delete(self, id, resource_id):

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
        return render('package/confirm_delete_resource.html')
