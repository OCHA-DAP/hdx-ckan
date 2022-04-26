import logging
import json
import collections

import ckan.authz as new_authz
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.helpers as hdx_helpers
import ckanext.hdx_theme.helpers.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

from ckanext.hdx_org_group.controller_logic.organization_search_logic import OrganizationSearchLogic
from ckanext.hdx_org_group.helpers.org_meta_dao import OrgMetaDao

get_action = tk.get_action
check_access = tk.check_access
config = tk.config
h = tk.h
NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)


class LightOrgReadLogic(object):
    def __init__(self, org_id, username, userobj):
        self.id = org_id
        self.username = username
        self.userobj = userobj

        self.redirect_result = None
        self.org_meta = None  # type OrgMetaDao
        self.search_template_data = None
        self.flask_route_name = 'hdx_light_org.light_read'

    def read(self):

        self.org_meta = self._fetch_org_metadata()
        org_dict = self.org_meta.org_dict

        if org_dict:
            search_logic = self._fetch_template_data(org_dict)
            self.search_template_data = search_logic.template_data

            self.redirect_result = search_logic.redirect_if_needed()
        return self

    def _fetch_org_metadata(self):
        '''
        :returns: The populated OrgMetaDao
        :rtype: OrgMetaDao
        '''
        org_meta = OrgMetaDao(self.id, self.username, self.userobj)
        org_meta.fetch_all()
        return org_meta

    def _fetch_template_data(self, org_dict):
        user = self.username
        ignore_capacity_check = False
        is_org_member = (user and new_authz.has_user_permission_for_group_or_org(org_dict.get('name'), user, 'read'))
        if is_org_member:
            ignore_capacity_check = True

        search_logic = OrganizationSearchLogic(org_dict.get('name'), self.flask_route_name,
                                               ignore_capacity_check=ignore_capacity_check)\
            .search().init_archived_url_helper()

        return search_logic


# Links = collections.namedtuple('Links', ['edit', 'members', 'request_membership', 'add_data'])


class OrgReadLogic(LightOrgReadLogic):

    def __init__(self, org_id, username, userobj):
        super(OrgReadLogic, self).__init__(org_id, username, userobj)
        self.flask_route_name = 'hdx_org.read'

        self.errors = []
        self.error_summary = ''
        self.top_line_items = None
        self.allow_basic_user_info = False
        self.allow_req_membership = False
        self.allow_edit = False
        self.allow_add_dataset = False

        self.follower_count = 0

        self.show_visualization = False

        # self.links = None  # type Links

        self.viz_config = {}

    def read(self):
        super(OrgReadLogic, self).read()
        if self.org_meta.is_custom and not self.redirect_result:
            self.top_line_items = self._fetch_topline_items()

            org_id = self.org_meta.org_dict['id']
            self.allow_basic_user_info = self.check_access('hdx_basic_user_info')
            self.allow_req_membership = not h.user_in_org_or_group(org_id) and self.allow_basic_user_info

            self.allow_edit = self.check_access('organization_update', {'id': org_id})
            self.allow_add_dataset = self.check_access('package_create', {
                'organization_id': org_id,
                'owner_org': org_id
            })
            self.viz_config = self._assemble_viz_config(self.org_meta.org_dict.get('visualization_config', ''), org_id)

            # self.links = Links(
            #     edit=h.url_for('organization.edit', id=org_id),
            #     members=h.url_for('hdx_members.members', id=org_id),
            #     request_membership=h.url_for('request_membership', org_id=org_id),
            #     add_data=h.url_for('add dataset') + '?organization_id={}'.format(org_id)
            # )

            self.follower_count = get_action('group_follower_count')(
                {'model': model, 'session': model.Session},
                {'id': org_id}
            )

            self.error_summary = '; '.join([e.get('message', '') for e in self.errors])

        return self

    def _fetch_topline_items(self):
        top_line_num_resource = self.org_meta.customization.get('topline_resource')

        top_line_items = []
        if top_line_num_resource:
            try:
                context = {'model': model, 'session': model.Session,
                           'user': self.username, 'for_view': True,
                           'auth_user_obj': self.userobj}
                top_line_src_dict = {
                    'top-line-numbers': {
                        'resource_id': top_line_num_resource
                    }
                }
                datastore_access = data_access.DataAccess(top_line_src_dict)
                datastore_access.fetch_data(context)
                top_line_items = datastore_access.get_top_line_items()

                formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
                formatter.format_results()

            except Exception as e:
                log.warning(e)
                hdx_helpers.add_error('Fetching data problem', str(e), self.errors)

        return top_line_items

    def _assemble_viz_config(self, vis_json_config, org_id=None):
        try:
            visualization = json.loads(vis_json_config)
        except Exception as e:
            log.warning(e)
            return "{}"

        config = {
            'title': visualization.get('viz-title', ''),
            'data_link_url': visualization.get('viz-data-link-url', '#'),
            'type': visualization.get('visualization-select', '')
        }

        # if visualization.get('visualization-select', '') == 'ROEA':
        #     config.update({
        #         'data': "/api/action/datastore_search?resource_id=" + visualization.get('viz-resource-id',
        #                                                                                 '') + "&limit=10000000",
        #         'geo': h.url_for('resource_download',
        #                          id=visualization.get('viz-geo-dataset-id', ''),
        #                          resource_id=visualization.get('viz-geo-resource-id', '')),
        #         'source': visualization.get('viz-data-source', '')
        #     })

        if visualization.get('visualization-select', '') == 'embedded' or visualization.get('visualization-select', '') == 'embedded-preview':
            config.update({
                'title': visualization.get('vis-title', ''),
                'data_link_url': visualization.get('vis-data-link-url', ''),
                'vis_url': visualization.get('vis-url', ''),
                'height': visualization.get('vis-height', '600px') if visualization.get('vis-height', '600px') != '' else '600px',
                'width': visualization.get('vis-width', '100%') if visualization.get('vis-width', '100%') != '' else '100%',
                'selector': visualization.get('vis-preview-selector', ''),
                'embedded_preview': h.url_for('hdx_local_image_server.org_file', filename=org_id + '_embedded_preview.png')
            })

        # if visualization.get('visualization-select', '') == 'WFP':
        #     config.update({
        #         'embedded': "true",
        #         'datastore_id': visualization.get('viz-resource-id', '')
        #     })

        # else:
        #     if visualization.get('datatype_1', '') == 'filestore':
        #         datatype = "filestore"
        #         data = h.url_for('resource_download',
        #                          id=visualization.get('dataset_id_1', ''),
        #                          resource_id=visualization.get('resource_id_1', ''))
        #     else:
        #         datatype = "datastore"
        #         data = "/api/action/datastore_search?resource_id=" + visualization.get('resource_id_1',
        #                                                                                '') + "&limit=10000000"
        #
        #     if visualization.get('datatype_2', '') == 'filestore':
        #         geotype = "filestore"
        #         geo = h.url_for('resource_download',
        #                         id=visualization.get('dataset_id_2', ''),
        #                         resource_id=visualization.get('resource_id_2', ''))
        #     else:
        #         geotype = "datastore"
        #         geo = "/api/action/datastore_search?resource_id=" + visualization.get('resource_id_2',
        #                                                                               '') + "&limit=10000000"
        #
        #     # beware that visualisation type constants are also used
        #     # in the template to select different resource bundles
        #     if visualization.get('visualization-select', '') == '3W-dashboard':
        #         config.update({'datatype': datatype,
        #                        'data': data,
        #                        'whoFieldName': visualization.get('who-column', ''),
        #                        'whatFieldName': visualization.get('what-column', ''),
        #                        'whereFieldName': visualization.get('where-column', ''),
        #                        'startFieldName': visualization.get('start-column', ''),
        #                        'endFieldName': visualization.get('end-column', ''),
        #                        'formatFieldName': visualization.get('format-column', ''),
        #                        'geotype': geotype,
        #                        'geo': geo,
        #                        'joinAttribute': visualization.get('where-column-2', ''),
        #                        'nameAttribute': visualization.get('map_district_name_column', ''),
        #                        'colors': visualization.get('colors', '')
        #                        })

        return config

    # def _get_embed_url(self):
    #     ckan_url = config.get('ckan.site_url', '').strip()
    #     position = ckan_url.find('//')
    #     if position >= 0:
    #         ckan_url = ckan_url[position:]
    #
    #     widget_url = ""
    #     if self.viz_config['type'] == '3W-dashboard':
    #         widget_url = "/widget/3W"
    #     if self.viz_config['type'] == 'WFP':
    #         widget_url = "/widget/WFP"
    #
    #     url = ckan_url + widget_url
    #     return url

    def check_access(self, action_name, data_dict=None):
        if data_dict is None:
            data_dict = {}

        context = {
            'model': model,
            'user': self.username
        }
        try:
            result = check_access(action_name, context, data_dict)
        except NotAuthorized:
            result = False

        return result
