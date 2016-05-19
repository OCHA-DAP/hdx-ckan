"""
    HDX Modifications to the default behavior of CKAN's dashboard
    for usersand user profiles. Overrides functions found in user.py

"""
import logging
import json

from pylons import config

import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
import ckan.new_authz as new_authz
import ckan.logic as logic
import ckan.common as common
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.controllers.user as uc
from ckan.controllers.api import CONTENT_TYPES

from ckan.common import _, c, g, request

import ckanext.hdx_search.controllers.search_controller as search_controller
import ckanext.hdx_theme.controllers.explorer as mpx

log = logging.getLogger(__name__)

abort = base.abort
render = base.render
validate = base.validate

check_access = logic.check_access
get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError

DataError = dictization_functions.DataError
unflatten = dictization_functions.unflatten

response = common.response

class DashboardController(uc.UserController, search_controller.HDXSearchController):
    def _get_dashboard_context(self, filter_type=None, filter_id=None, q=None):
        '''Return a dict needed by the dashboard view to determine context.'''

        def display_name(followee):
            '''Return a display name for a user, group or dataset dict.'''
            display_name = followee.get('display_name')
            fullname = followee.get('fullname')
            title = followee.get('title')
            name = followee.get('name')
            return display_name or fullname or title or name

        if (filter_type and filter_id):
            context = {
                'model': model, 'session': model.Session,
                'user': c.user or c.author, 'auth_user_obj': c.userobj,
                'for_view': True
            }

            data_dict = {'id': filter_id}
            followee = None

            action_functions = {
                'dataset': 'package_show',
                'user': 'user_show',
                'group': 'group_show',
                'organization': 'organization_show'  # ADD BY HDX
            }
            action_function = logic.get_action(
                action_functions.get(filter_type))
            # Is this a valid type?
            if action_function is None:
                abort(404, _('Follow item not found'))
            try:
                followee = action_function(context, data_dict)
            except NotFound:
                abort(404, _('{0} not found').format(filter_type))
            except NotAuthorized:
                abort(401, _('Unauthorized to read {0} {1}').format(
                    filter_type, id))
            if followee is not None:
                return {
                    'filter_type': filter_type,
                    'q': q,
                    'context': display_name(followee),
                    'selected_id': followee.get('id'),
                    'dict': followee,
                }

        return {
            'filter_type': filter_type if filter_type else 'dashboard',  # CHANGED BY HDX
            'q': q,
            'context': _('Everything'),
            'selected_id': False,
            'dict': None,
        }

    def read(self, id=None):
        """
        Identical to user.py:read, but needs to be here to receive requests
        and direct them to the correct _setup_template_variables method
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj,
                     'include_datasets': True,
                     'include_num_followers': True}

        context['with_related'] = True

        self._setup_template_variables(context, data_dict)

        # The legacy templates have the user's activity stream on the user
        # profile page, new templates do not.
        if h.asbool(config.get('ckan.legacy_templates', False)):
            c.user_activity_stream = get_action('user_activity_list_html')(
                context, {'id': c.user_dict['id']})

        return render('user/read.html')

    def _setup_template_variables(self, context, data_dict):
        """
        Sets up template variables. If the user is deleted, throws a 404
        unless the user is logged in as sysadmin.
        """
        c.is_sysadmin = new_authz.is_sysadmin(c.user)
        try:
            user_dict = get_action('user_show')(context, data_dict)
        except NotFound:
            abort(404, _('User not found'))
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))
        if user_dict['state'] == 'deleted' and not c.is_sysadmin:
            abort(404, _('User not found'))
        c.user_dict = user_dict
        c.is_myself = user_dict['name'] == c.user
        c.about_formatted = h.render_markdown(user_dict['about'])

    def dashboard_activity_stream(self, user_id, filter_type=None, filter_id=None,
                                  offset=0):
        '''Return the dashboard activity stream of the current user.

        :param user_id: the id of the user
        :type user_id: string

        :param filter_type: the type of thing to filter by
        :type filter_type: string

        :param filter_id: the id of item to filter by
        :type filter_id: string

        :returns: an activity stream as an HTML snippet
        :rtype: string

        '''
        context = {'model': model, 'session': model.Session, 'user': c.user}

        if filter_type:
            action_functions = {
                'dataset': 'package_activity_list_html',
                'user': 'user_activity_list_html',
                'group': 'group_activity_list_html',
                'organization': 'organization_activity_list_html'  # ADDED BY HDX
            }
            action_function = logic.get_action(action_functions.get(filter_type))
            return action_function(context, {'id': filter_id, 'offset': offset})
        else:
            return logic.get_action('dashboard_activity_list_html')(
                context, {'offset': offset})

    def dashboard(self, id=None, offset=0):
        """
        Display basic dashboard, creates a filter for organizations
        to pass onto the template that is not included in CKAN core
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {'id': id, 'user_obj': c.userobj, 'offset': offset}
        try:
            user_dict = get_action('user_show')(context, data_dict)
        except NotFound:
            came_from = h.url_for(controller='user', action='dashboard', __ckan_no_root=True)
            h.redirect_to(controller='user',
                              action='login', came_from=came_from)
        self._setup_template_variables(context, data_dict)

        q = request.params.get('q', u'')
        filter_type = request.params.get('type', u'')
        filter_id = request.params.get('name', u'')
        try:
            if filter_type == 'group':
                c.group_dict = logic.get_action('organization_show')(context, {'id': filter_id})  # patch for db entries
                if c.group_dict['is_organization']:
                    filter_type = 'organization'
        except:
            filter_type = filter_type
        c.followee_list = get_action('followee_list')(
            context, {'id': c.userobj.id, 'q': q})
        c.dashboard_activity_stream_context = self._get_dashboard_context(
            filter_type, filter_id, q)
        c.dashboard_activity_stream = self.dashboard_activity_stream(c.userobj.id, filter_type, filter_id, offset)

        # Mark the user's new activities as old whenever they view their
        # dashboard page.
        get_action('dashboard_mark_activities_old')(context, {})
        return render('user/dashboard.html')

    def dashboard_datasets(self):
        """
        Dashboard tab for datasets. Modified to add the ability to change
        the order and ultimately filter datasets displayed
        """

        context = {'model': model, 'session': model.Session, 'for_view': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   # Do NOT fetch the datasets we will fetch via package_search
                   'return_minimal': True,  # This is being deprecated
                   'include_num_followers': False,
                   'include_datasets': False
                   }
        data_dict = {'user_obj': c.userobj}

        try:
            user_dict = get_action('user_show')(context, data_dict)
        except NotFound:
            came_from = h.url_for(controller='user', action='dashboard_datasets', __ckan_no_root=True)
            h.redirect_to(controller='user', action='login', came_from=came_from)

        try:
            page = int(request.params.get('page', 1))
        except ValueError, e:
            abort(400, ('"page" parameter must be an integer'))
        limit = 20
        data_dict['limit'] = limit
        data_dict['offset'] = (page - 1) * limit
        data_dict['sort'] = request.params.get('sort', 'metadata_modified desc')
        c.sort_by_selected = data_dict['sort']
        c.is_sysadmin = new_authz.is_sysadmin(c.user)
        try:
            user_dict = get_action('hdx_user_show')(context, data_dict)
            c.active_datasets = [dataset for dataset in user_dict.get('datasets', []) if
                               dataset.get('state', 'deleted') == 'active']
        except NotFound:
            abort(404, _('User not found'))
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        c.is_myself = user_dict['name'] == c.user
        if self._is_facet_only_request():
            c.full_facet_info = self._get_dataset_search_results(user_dict['id'])
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)

        else:
            c.user_dict = user_dict
            c.about_formatted = h.render_markdown(user_dict['about'])

            c.full_facet_info = self._get_dataset_search_results(user_dict['id'])

            return render('user/dashboard_datasets.html')

    def dashboard_visualizations(self):
        """
        Dashboard tab for visualizations.
        """

        context = {'model': model, 'session': model.Session, 'for_view': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   }
        if c.userobj:
            id = c.userobj.id
        else:
            id = None
        data_dict = {'id': id, 'user_obj': c.userobj}

        user_dict = None
        powerviews = None
        #check if user can access this link
        try:
            user_dict = get_action('user_show')(context, data_dict)
        except NotFound:
            came_from = h.url_for(controller='user', action='dashboard_visualizations', __ckan_no_root=True)
            h.redirect_to(controller='user', action='login', came_from=came_from)

        try:
            powerviews = get_action('powerview_list')(context, data_dict)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        template_data = {
            'data': {
                'user_dict': user_dict,
                'powerviews': powerviews,
                'mpx_url_template': config.get('hdx.explorer.url')+mpx.get_powerview_load_url("")
            }
        }
        return render('user/dashboard_visualizations.html', extra_vars=template_data)

    def hdx_delete_powerview(self, id):
        """
        Dashboard tab for visualizations.
        """

        context = {'model': model, 'session': model.Session, 'for_view': True,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   }
        data_dict = {'id': id, 'user_obj': c.userobj}

        #check if user can access this link
        # try:
        #     check_access('powerview_delete', context, data_dict)
        # except NotAuthorized:
        #     base.abort(401, _('Unauthorized to request reset password.'))

        try:
            get_action('powerview_delete')(context, data_dict)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        h.redirect_to(controller='ckanext.hdx_users.controllers.dashboard_controller:DashboardController', action='dashboard_visualizations')
        # return self.dashboard_visualizations()


    def _get_dataset_search_results(self, user_id):

        ignore_capacity_check = False
        if c.is_myself:
            ignore_capacity_check = True

        package_type = 'dataset'

        suffix = '#datasets-section'

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('user_dashboard_datasets', **params) + suffix

        fq = 'creator_user_id:"{}"'.format(user_id)

        full_facet_info = self._search(package_type, pager_url, additional_fq=fq,
                                       ignore_capacity_check=ignore_capacity_check)

        c.other_links['current_page_url'] = h.url_for('user_dashboard_datasets')

        return full_facet_info


