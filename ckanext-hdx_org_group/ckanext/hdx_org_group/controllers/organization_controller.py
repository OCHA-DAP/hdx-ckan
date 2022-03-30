# '''
# Created on Jan 13, 2015
#
# @author: alexandru-m-g
# '''
#
# import itertools
# import json
# import logging
#
# import ckan.authz as new_authz
# import ckan.common as common
# import ckan.controllers.organization as org
# import ckan.lib.base as base
# import ckan.lib.helpers as h
# import ckan.lib.navl.dictization_functions as dict_fns
# import ckan.logic as logic
# import ckan.model as model
# import ckanext.hdx_org_group.controllers.custom_org_controller as custom_org
# import ckanext.hdx_org_group.dao.common_functions as common_functions
# import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
# import ckanext.hdx_org_group.helpers.organization_helper as helper
# import ckanext.hdx_org_group.helpers.static_lists as static_lists
# import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
# import ckanext.hdx_theme.util.jql as jql
# from ckan.common import c, request, _
# from ckan.controllers.api import CONTENT_TYPES
# from ckanext.hdx_theme.util.light_redirect import check_redirect_needed
#
# abort = base.abort
# render = base.render
#
# NotFound = logic.NotFound
# NotAuthorized = logic.NotAuthorized
# ValidationError = logic.ValidationError
# tuplize_dict = logic.tuplize_dict
# clean_dict = logic.clean_dict
# parse_params = logic.parse_params
# get_action = logic.get_action
#
# response = common.response
#
# log = logging.getLogger(__name__)


# def is_not_custom(environ, result):
#     '''
#     check if location is a custom one and/or contains visual customizations
#     :param environ:
#     :param result:
#     :return:
#     '''
#     org_meta = org_meta_dao.OrgMetaDao(result['id'])
#     org_meta.fetch_org_dict()
#     result['org_meta'] = org_meta
#     if org_meta.is_custom:
#         return False
#     return True


# class HDXOrganizationController(org.OrganizationController):
    # def index(self):
    #     context = {'model': model, 'session': model.Session,
    #                'for_view': True,
    #                'with_private': False}
    #
    #     try:
    #         self._check_access('site_read', context)
    #     except NotAuthorized:
    #         abort(403, _('Not authorized to see this page'))
    #
    #     # pass user info to context as needed to view private datasets of
    #     # orgs correctly
    #     # if c.userobj:
    #     #     context['user_id'] = c.userobj.id
    #     #     context['user_is_admin'] = c.userobj.sysadmin
    #     #     context['auth_user_obj'] = c.userobj
    #
    #     try:
    #         q = c.q = request.params.get('q', '')
    #         page = int(request.params.get('page', 1))
    #         limit = int(request.params.get('limit', 25))
    #         sort_option = request.params.get('sort', 'title asc')
    #     except ValueError:
    #         abort(404, 'Page not found')
    #
    #     reset_thumbnails = request.params.get('reset_thumbnails', 'false')
    #
    #     data_dict = {
    #         'all_fields': True,
    #         'sort': sort_option if sort_option in ['title asc', 'title desc'] else 'title asc',
    #         # Custom sorts will throw an error here
    #         'q': q,
    #         'reset_thumbnails': reset_thumbnails,
    #     }
    #
    #     all_orgs = get_action('cached_organization_list')(context, data_dict)
    #
    #     all_orgs = helper.filter_and_sort_results_case_insensitive(all_orgs, sort_option, q=q, has_datasets=True)
    #
    #     # c.featured_orgs = helper.hdx_get_featured_orgs(context, data_dict)
    #
    #     def pager_url(page=None):
    #         if sort_option:
    #             url = h.url_for(
    #                 'organizations_index', q=q, page=page, sort=sort_option, limit=limit) + '#organizationsSection'
    #         else:
    #             url = h.url_for('organizations_index', q=q, page=page, limit=limit) + '#organizationsSection'
    #         return url
    #
    #     c.page = h.Page(
    #         collection=all_orgs,
    #         page=page,
    #         url=pager_url,
    #         items_per_page=limit
    #     )
    #
    #     # displayed_orgs = c.featured_orgs + [o for o in c.page]
    #     displayed_orgs = [o for o in c.page]
    #     helper.org_add_last_updated_field(displayed_orgs)
    #
    #     return base.render('organization/index.html')

    # @check_redirect_needed
    # def read(self, id, limit=20):
    #     self._ensure_controller_matches_group_type(id)
    #
    #     # unicode format (decoded from utf8)
    #     q = c.q = request.params.get('q', '')
    #
    #     c.org_meta = org_meta = org_meta_dao.OrgMetaDao(id, c.user or c.author, c.userobj)
    #     try:
    #         org_meta.fetch_all()
    #     except NotFound, e:
    #         abort(404)
    #     except NotAuthorized, e:
    #         abort(403, _('Not authorized to see this page'))
    #
    #     helper.org_add_last_updated_field([org_meta.org_dict])
    #
    #     c.group_dict = org_meta.org_dict
    #
    #     # If custom_org set to true, redirect to the correct route
    #     if org_meta.is_custom:
    #         custom_org_controller = custom_org.CustomOrgController()
    #         return custom_org_controller.org_read(id, org_meta)
    #     else:
    #         org_info = self._get_org(id)
    #         c.full_facet_info = self._get_dataset_search_results(org_info['name'])
    #
    #         # setting the count with the value that was populated from search_controller so that templates find it
    #         c.group_dict['package_count'] = c.count
    #         c.group_dict['type'] = 'organization'
    #
    #         # This was moved in OrgMetaDao
    #         # allow_basic_user_info = self.check_access('hdx_basic_user_info')
    #         # allow_req_membership = not h.user_in_org_or_group(org_info['id']) and allow_basic_user_info
    #         # c.request_membership = allow_req_membership
    #         # c.request_membership_url = h.url_for('request_membership', org_id=org_info['id'])
    #
    #         if self._is_facet_only_request():
    #             response.headers['Content-Type'] = CONTENT_TYPES['json']
    #             return json.dumps(c.full_facet_info)
    #         else:
    #             # self._read(id, limit)
    #             return render(self._read_template(c.group_dict['type']),
    #                       {'group_dict': c.group_dict})

    # def _get_org(self, org_id):
    #     group_type = 'organization'
    #
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'schema': self._db_to_form_schema(group_type=group_type),
    #                'for_view': True}
    #     data_dict = {'id': org_id}
    #
    #     try:
    #         context['include_datasets'] = False
    #         result = get_action(
    #             'hdx_light_group_show')(context, data_dict)
    #
    #         return result
    #
    #     except NotFound:
    #         abort(404, _('Org not found'))
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to read org %s') % id)
    #
    #     return {}

    # def _get_dataset_search_results(self, org_code):
    #
    #     user = c.user or c.author
    #     ignore_capacity_check = False
    #     is_org_member = (user and
    #                      new_authz.has_user_permission_for_group_or_org(org_code, user, 'read'))
    #     if is_org_member:
    #         ignore_capacity_check = True
    #
    #     package_type = 'dataset'
    #
    #     suffix = '#datasets-section'
    #
    #     params_nopage = {
    #         k: v for k, v in request.params.items() if k != 'page'}
    #
    #     def pager_url(q=None, page=None):
    #         params = params_nopage
    #         params['page'] = page
    #         return h.url_for('organization_read', id=org_code, **params) + suffix
    #
    #     fq = 'organization:"{}"'.format(org_code)
    #
    #     full_facet_info = self._search(package_type, pager_url, additional_fq=fq,
    #                                    ignore_capacity_check=ignore_capacity_check)
    #     full_facet_info.get('facets', {}).pop('organization', {})
    #
    #     base_url = h.url_for('organization_read', id=org_code)
    #     c.other_links['current_page_url'] = base_url
    #     archived_url_helper = self.add_archived_url_helper(full_facet_info, base_url)
    #     archived_url_helper.redirect_if_needed()
    #
    #     return full_facet_info

    # def new(self, data=None, errors=None, error_summary=None):
    #     group_type = self._guess_group_type(True)
    #     if data:
    #         data['type'] = group_type
    #
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'save': 'save' in request.params,
    #                'parent': request.params.get('parent', None)}
    #     try:
    #         self._check_access('group_create', context)
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to create a group'))
    #
    #     if context['save'] and not data:
    #         return self._save_new(context, group_type)
    #
    #     data = data or {}
    #     if not data.get('image_url', '').startswith('http'):
    #         data.pop('image_url', None)
    #
    #     errors = errors or {}
    #     error_summary = error_summary or {}
    #     vars = {'data': data, 'errors': errors,
    #             'error_summary': error_summary, 'action': 'new'}
    #
    #     self._setup_template_variables(context, data, group_type=group_type)
    #     c.hdx_org_type_list = [{'value': '-1', 'text': _('-- Please select --')}] + \
    #                           [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]
    #     c.form = render(self._group_form(group_type=group_type),
    #                     extra_vars=vars)
    #     return render(self._new_template(group_type))

    # def edit(self, id, data=None, errors=None, error_summary=None):
    #     group_type = 'organization'
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'save': 'save' in request.params,
    #                'restore': 'restore' in request.params,
    #                'for_edit': True,
    #                'parent': request.params.get('parent', None)
    #                }
    #     data_dict = {'id': id}
    #
    #     if context['save'] and not data:
    #         return self._save_edit(id, context)
    #     if context['restore'] and not data:
    #         return self._restore_org(id, context)
    #
    #     try:
    #         old_data = self._action('group_show')(context, data_dict)
    #         c.grouptitle = old_data.get('title')
    #         c.groupname = old_data.get('name')
    #         data = data or old_data
    #     except NotFound:
    #         abort(404, _('Group not found'))
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to read group %s') % '')
    #
    #     group = context.get("group")
    #     c.group = group
    #     c.group_dict = self._action('group_show')(context, data_dict)
    #
    #     try:
    #         self._check_access('group_update', context)
    #     except NotAuthorized, e:
    #         abort(403, _('User %r not authorized to edit %s') % (c.user, id))
    #
    #     errors = errors or {}
    #     vars = {'data': data, 'errors': errors,
    #             'error_summary': error_summary, 'action': 'edit'}
    #
    #     self._setup_template_variables(context, data, group_type=group_type)
    #     c.hdx_org_type_list = [{'value': '-1', 'text': _('-- Please select --')}] +\
    #                           [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]
    #     form = render(self._group_form(group_type), extra_vars=vars)
    #
    #     #  The extra_vars are needed here to send analytics information like org name and id
    #     extra_vars = {
    #         'data': data,
    #         'form': form,
    #         'group_type': group_type
    #     }
    #     return render(self._edit_template(c.group.type), extra_vars=extra_vars)

    # def stats(self, id, org_meta=None, offset=0):
    #     if not org_meta:
    #         org_meta = org_meta_dao.OrgMetaDao(id, c.user or c.author, c.userobj)
    #     c.org_meta = org_meta
    #     org_meta.fetch_all()
    #     helper.org_add_last_updated_field([org_meta.org_dict])
    #     c.group_dict = org_meta.org_dict
    #
    #     # Add the group's activity stream (already rendered to HTML) to the
    #     # template context for the group/read.html template to retrieve later.
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author, 'for_view': True}
    #
    #     org_id = org_meta.org_dict['id']
    #     org_name = org_meta.org_dict.get('name')
    #     pageviews_per_week_dict = jql.pageviews_per_organization_per_week_last_24_weeks_cached().get(
    #         org_id, {})
    #     downloads_per_week_dict = jql.downloads_per_organization_per_week_last_24_weeks_cached().get(
    #         org_id, {})
    #
    #     dw_and_pv_per_week = []
    #     for date_str in pageviews_per_week_dict.keys():
    #         dw_and_pv_per_week.append({
    #             'org_id': org_id,
    #             'date': date_str,
    #             'pageviews': pageviews_per_week_dict[date_str].get('value', 0),
    #             'downloads': downloads_per_week_dict.get(date_str, {}).get('value', 0)
    #         })
    #
    #     stats_top_dataset_downloads, total_downloads_topline, stats_1_dataset_downloads_last_weeks, stats_1_dataset_name = \
    #         self._stats_top_dataset_downloads(org_id, org_name)
    #
    #     downloaders_topline = jql.downloads_per_organization_last_30_days_cached().get(org_id, 0)
    #     viewers_topline = jql.pageviews_per_organization_last_30_days_cached().get(org_id, 0)
    #     template_data = {
    #         'data': {
    #             'stats_downloaders': self._format_topline(downloaders_topline),
    #             'stats_viewers': self._format_topline(viewers_topline),
    #             'stats_top_dataset_downloads': stats_top_dataset_downloads,
    #             'stats_total_downloads': self._format_topline(total_downloads_topline, unit='count'),
    #             'stats_1_dataset_downloads_last_weeks': stats_1_dataset_downloads_last_weeks,
    #             'stats_1_dataset_name': stats_1_dataset_name,
    #             'stats_dw_and_pv_per_week': dw_and_pv_per_week
    #         },
    #         'group_dict': c.group_dict
    #     }
    #
    #     if org_meta.is_custom:
    #         return render('organization/custom_stats.html', extra_vars=template_data)
    #     else:
    #         return render('organization/stats.html', extra_vars=template_data)

    # def _format_topline(self, topline_value, unit=None):
    #     '''
    #     :param topline_value:
    #     :type topline_value: int
    #     :return: dict with formatted value (as string) and unit
    #     :rtype: dict
    #     '''
    #     if not unit:
    #         unit = common_functions.compute_simplifying_units(topline_value)
    #
    #     topline = [{
    #         'units': unit,
    #         'value': topline_value
    #     }]
    #
    #     formatters.TopLineItemsFormatter(topline).format_results()
    #     result = topline[0]
    #     if result.get('units') == 'count':
    #         result['units'] = ''
    #     return result

    # def _stats_top_dataset_downloads(self, org_id, org_name):
    #     from ckan.lib.search.query import make_connection
    #     datasets_map = jql.downloads_per_organization_per_dataset_last_24_weeks_cached().get(
    #         org_id, {})
    #     total_downloads = sum((item.get('value') for item in datasets_map.values()))
    #
    #     data_dict = {
    #         'q': '*:*',
    #         'fl': 'id name title',
    #         'fq': 'capacity:"public" organization:{}'.format(org_name),
    #         'rows': 5000, # Just setting a max, we need all public datasets that an org has
    #         'start': 0,
    #     }
    #
    #     ret = []
    #     if datasets_map:
    #         mp_datasets_sorted = sorted(datasets_map.values(), key=lambda item: item.get('value'), reverse=True)
    #         try:
    #             conn = make_connection(decode_dates=False)
    #             search_result = conn.search(**data_dict)
    #             dataseta_meta_map = {
    #                 d['id']: {
    #                     'title': d.get('title'),
    #                     'name': d.get('name'),
    #                 }
    #                 for d in search_result.docs
    #             }
    #             ret = [
    #                 {
    #                     'dataset_id': d.get('dataset_id'),
    #                     'name': dataseta_meta_map.get(d.get('dataset_id'), {}).get('title'),
    #                     'url': h.url_for('dataset_read', id=dataseta_meta_map.get(d.get('dataset_id'), {}).get('name')),
    #                     'value': d.get('value'),
    #                     'total': total_downloads,
    #                     # 'percentage': round(100*d.get('value', 0)/total_downloads, 1)
    #                 }
    #                 for d in itertools.islice(
    #                     (ds for ds in mp_datasets_sorted if ds.get('dataset_id') in dataseta_meta_map), 25
    #                 )
    #             ]
    #         except Exception, e:
    #             log.warn('Error in searching solr {}'.format(str(e)))
    #
    #     # query = get_action('package_search')(context, data_dict)
    #     stats_1_dataset_downloads_last_weeks = []
    #     stats_1_dataset_name = None
    #     if ret and len(ret) == 1:
    #         dataset_id = ret[0].get('dataset_id')
    #         stats_1_dataset_downloads_last_weeks = \
    #             jql.fetch_downloads_per_week_for_dataset(dataset_id).values()
    #         stats_1_dataset_name = ret[0].get('name')
    #
    #     return ret, total_downloads, stats_1_dataset_downloads_last_weeks, stats_1_dataset_name

    # def check_access(self, action_name, data_dict=None):
    #     if data_dict is None:
    #         data_dict = {}
    #
    #     context = {'model': model,
    #                'user': c.user or c.author}
    #     try:
    #         result = logic.check_access(action_name, context, data_dict)
    #     except logic.NotAuthorized:
    #         result = False
    #
    #     return result

    # def activity_stream(self, id, org_meta=None, offset=0):
    #     '''
    #      Modified core functionality to use the new OrgMetaDao class
    #     for fetching information needed on all org-related pages.
    #
    #     Render this group's public activity stream page.
    #
    #     :param id:
    #     :type id: str
    #     :param offset:
    #     :type offset: int
    #     :param org_meta:
    #     :type org_meta: org_meta_dao.OrgMetaDao
    #     :return:
    #     '''
    #     if not org_meta:
    #         org_meta = org_meta_dao.OrgMetaDao(id, c.user or c.author, c.userobj)
    #     c.org_meta = org_meta
    #     org_meta.fetch_all()
    #     helper.org_add_last_updated_field([org_meta.org_dict])
    #     c.group_dict = org_meta.org_dict
    #
    #     # Add the group's activity stream (already rendered to HTML) to the
    #     # template context for the group/read.html template to retrieve later.
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author, 'for_view': True}
    #     c.group_activity_stream = get_action('organization_activity_list')(
    #         context, {'id': c.group_dict['id'], 'offset': offset})
    #
    #     extra_vars = {'group_dict': c.group_dict}
    #     if org_meta.is_custom:
    #         return render(custom_org.CustomOrgController()._activity_template('organization'), extra_vars)
    #     else:
    #         return render(self._activity_template('organization'), extra_vars)
    #
    # def _restore_org(self, id, context):
    #
    #     try:
    #         self._check_access('organization_delete', context)
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to restore this organization'))
    #
    #     try:
    #         data_dict = clean_dict(dict_fns.unflatten(
    #             tuplize_dict(parse_params(request.params))))
    #         context['message'] = data_dict.get('log_message', '')
    #         data_dict['id'] = id
    #         context['allow_partial_update'] = True
    #         data_dict['state'] = 'active'
    #         group = self._action('group_update')(context, data_dict)
    #         if id != group['name']:
    #             self._force_reindex(group)
    #         h.redirect_to('%s_read' % group['type'], id=group['name'])
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to read group %s') % id)
    #     except NotFound, e:
    #         abort(404, _('Group not found'))
    #     except dict_fns.DataError:
    #         abort(400, _(u'Integrity Error'))
    #     except ValidationError, e:
    #         errors = e.error_dict
    #         error_summary = e.error_summary
    #         return self.edit(id, data_dict, errors, error_summary)

    # def feed_organization(self, id):
    #     try:
    #         context = {'model': model, 'session': model.Session,
    #                    'user': c.user, 'auth_user_obj': c.userobj}
    #         group_dict = logic.get_action('organization_show')(context,
    #                                                            {'id': id})
    #     except logic.NotFound:
    #         base.abort(404, _('Organization not found'))
    #     except logic.NotAuthorized:
    #         base.abort(404, _('Organization not found'))
    #     fc = FeedController()
    #     return fc._group_or_organization(group_dict, is_org=True)
