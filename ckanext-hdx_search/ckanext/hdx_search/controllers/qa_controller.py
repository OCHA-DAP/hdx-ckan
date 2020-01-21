import logging
from urllib import urlencode

import sqlalchemy
from botocore.exceptions import ClientError
from pylons import config

import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_package.helpers.membership_data as membership
import ckanext.hdx_search.helpers.search_history as search_history

from ckan.common import _, json, request, c, response
from ckan.controllers.api import CONTENT_TYPES
from ckanext.hdx_search.controllers.search_controller import HDXSearchController
from ckanext.hdx_search.helpers.constants import NEW_DATASETS_FACET_NAME, UPDATED_DATASETS_FACET_NAME,\
    DELINQUENT_DATASETS_FACET_NAME, BULK_DATASETS_FACET_NAME
from ckanext.hdx_search.helpers.qa_s3 import LogS3
from ckanext.hdx_search.helpers.solr_query_helper import generate_datetime_period_query
from ckanext.hdx_search.helpers.qa_data import questions_list as qa_data_questions_list
from ckanext.hdx_theme.helpers.json_transformer import get_obj_from_json_in_dict

_validate = dict_fns.validate

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text

log = logging.getLogger(__name__)

render = tk.render
abort = tk.abort

NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError
get_action = tk.get_action
check_access = tk.check_access
redirect = tk.redirect_to


NUM_OF_ITEMS = 25

STATUS_PRIORITIES = {
    '': 0,
    'OK': 1,
    'RUNNING': 2,
    'QUEUED': 3,
    'ERROR': 4
}


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


class HDXQAController(HDXSearchController):
    def search(self):
        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('qa_dashboard_show', context)
        except (NotFound, NotAuthorized):
            abort(404, _('Not authorized to see this page'))

        package_type = 'dataset'

        params_nopage = self._params_nopage()
        c.search_url_params = urlencode(_encode_params(params_nopage))

        c.membership = membership.get_membership_by_user(c.user or c.author, None, c.userobj)

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            url = h.url_for('qa_dashboard')
            params = _encode_params(params)
            return url + u'?' + urlencode(params)

        c.full_facet_info = self._search(package_type, pager_url)

        c.cps_off = config.get('hdx.cps.off', 'false')
        c.other_links['current_page_url'] = h.url_for('qa_dashboard')
        query_string = request.params.get('q', u'')
        if c.userobj and query_string:
            search_history.store_search(query_string, c.userobj.id)

        # If we're only interested in the facet numbers a json will be returned with the numbers
        if self._is_facet_only_request():
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            self._setup_template_variables(context, {},
                                           package_type=package_type)
            return self._search_template()

    def qa_pii_log(self, id, resource_id):
        self._redirect_to_qa_log(resource_id, 'pii.log.txt')

    def qa_sdcmicro_log(self, id, resource_id):
        self._redirect_to_qa_log(resource_id, 'sdc.log.txt')

    def _redirect_to_qa_log(self, resource_id, log_filename):
        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('qa_dashboard_show', context)
        except (NotFound, NotAuthorized):
            abort(404, _('Not authorized to see this page'))
        try:
            path = 'resources/{resource_id}/{log_filename}'.format(resource_id=resource_id, log_filename=log_filename)
            uploader = LogS3()
            s3 = uploader.get_s3_session()
            client = s3.client(service_name='s3', endpoint_url=uploader.host_name)
            url = client.generate_presigned_url(ClientMethod='get_object',
                                                Params={'Bucket': uploader.bucket_name,
                                                        'Key': path},
                                                ExpiresIn=60)
            redirect(url)

        except ClientError as ex:
            log.error(str(ex))

    def _add_additional_faceting_queries(self, search_data_dict):
        super(HDXQAController, self)._add_additional_faceting_queries(search_data_dict)
        new_datasets_query = generate_datetime_period_query('metadata_created', last_x_days=7)
        updated_datasets_query = generate_datetime_period_query('metadata_modified', last_x_days=7)
        delinquent_datasets_query = generate_datetime_period_query('delinquent_date')
        updated_by_script_query = 'extras_updated_by_script:[* TO *]'

        facet_queries = search_data_dict.get('facet.query') or []
        facet_queries.append('{{!key={} ex=batch}} {}'.format(NEW_DATASETS_FACET_NAME, new_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(UPDATED_DATASETS_FACET_NAME, updated_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(DELINQUENT_DATASETS_FACET_NAME,
                                                              delinquent_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(BULK_DATASETS_FACET_NAME, updated_by_script_query))
        search_data_dict['facet.query'] = facet_queries

        search_data_dict['facet.field'].append('qa_completed')
        search_data_dict['f.qa_completed.facet.missing'] = 'true'

    # def _generate_facet_name_to_title_map(self, package_type):
    #     facets = super(HDXQAController, self)._generate_facet_name_to_title_map(package_type)
    #     facets['qa_completed'] = 'QA completed'
    #     return facets

    def _process_complex_facet_data(self, existing_facets, title_translations, result_facets, search_extras):
        super(HDXQAController, self)._process_complex_facet_data(existing_facets, title_translations, result_facets,
                                                                 search_extras)

        if existing_facets:
            item_list = []
            result_facets['qa_only'] = {
                'name': 'qa_only',
                'display_name': _('QA only'),
                'items': item_list,
                'show_everything': True
            }

            self.__add_facet_item_to_list(NEW_DATASETS_FACET_NAME, _('New datasets'), existing_facets,
                                          item_list, search_extras)
            self.__add_facet_item_to_list(UPDATED_DATASETS_FACET_NAME, _('Updated datasets'), existing_facets,
                                          item_list, search_extras)
            self.__add_facet_item_to_list(DELINQUENT_DATASETS_FACET_NAME, _('Delinquent datasets'), existing_facets,
                                          item_list, search_extras)
            self.__add_facet_item_to_list(BULK_DATASETS_FACET_NAME, _('Bulk upload'), existing_facets,
                                          item_list, search_extras)

            self.__process_qa_completed_facet(existing_facets, title_translations, search_extras, item_list)

    def __add_facet_item_to_list(self, item_name, item_display_name, existing_facets, qa_only_item_list, search_extras):
        category_key = 'ext_' + item_name
        item = next(
            (i for i in existing_facets.get('queries', []) if i.get('name') == item_name), None)
        item['display_name'] = item_display_name
        item['category_key'] = category_key
        item['name'] = '1'  # this gets displayed as value in HTML <input>
        item['selected'] = search_extras.get(category_key)
        qa_only_item_list.append(item)

    def __process_qa_completed_facet(self, existing_facets, title_translations, search_extras, qa_only_item_list):
        title_translations.pop('qa_completed', None)

        facet_data = existing_facets.pop('qa_completed', {})
        qa_completed_item = next(
            (i for i in facet_data.get('items', []) if i.get('name') == 'true'),
            {}
        )

        qa_category_key = 'ext_qa_completed'
        qa_completed_item['category_key'] = qa_category_key
        qa_completed_item['display_name'] = 'QA Completed'
        qa_completed_item['name'] = '1'
        qa_completed_item['count'] = qa_completed_item.get('count', 0)
        qa_completed_item['selected'] = search_extras.get(qa_category_key) == '1'

        qa_only_item_list.append(qa_completed_item)

        qa_not_completed_count = sum(
            (i.get('count', 0) for i in facet_data.get('items', []) if i.get('name') != 'true')
        )
        qa_not_completed_item = {}
        qa_not_completed_item['category_key'] = qa_category_key
        qa_not_completed_item['display_name'] = 'QA Not Completed'
        qa_not_completed_item['name'] = '0'
        qa_not_completed_item['count'] = qa_not_completed_count
        qa_not_completed_item['selected'] = search_extras.get(qa_category_key) == '0'
        qa_only_item_list.append(qa_not_completed_item)

    def _process_found_package_list(self, package_list):

        self.__process_checklist_data(package_list)
        self.__process_script_check_data(package_list, 'pii_report_flag', 'pii_timestamp')
        self.__process_script_check_data(package_list, 'sdc_report_flag', 'sdc_timestamp')

    def __process_checklist_data(self, package_list):

        if package_list:
            num_of_resource_questions = len(qa_data_questions_list['resources_checklist'])
            num_of_package_questions = len(qa_data_questions_list['data_protection_checklist']) + \
                                       len(qa_data_questions_list['metadata_checklist'])

            for package_dict in package_list:
                resource_list = package_dict.get('resources', [])
                checklist = get_obj_from_json_in_dict(package_dict, 'qa_checklist')
                package_dict['qa_checklist'] = checklist
                package_dict['qa_checklist_num'] = len(checklist.get('dataProtection', [])) + \
                                                   len(checklist.get('metadata', []))
                package_dict['qa_checklist_total_num'] = num_of_package_questions + \
                                                         num_of_resource_questions * len(resource_list)

                for r in resource_list:
                    r['qa_checklist'] = get_obj_from_json_in_dict(r, 'qa_checklist')
                    r['qa_checklist_num'] = len(r['qa_checklist'])
                    package_dict['qa_checklist_num'] += r['qa_checklist_num']
                    r['qa_checklist_total_num'] = num_of_resource_questions

    def __process_script_check_data(self, package_list, report_flag_field, timestamp_field):

        if package_list:
            for package_dict in package_list:
                resource_list = package_dict.get('resources', [])
                package_dict[report_flag_field] = ''
                package_dict[timestamp_field] = ''
                package_pii_priority = 0
                for r in resource_list:
                    res_pii_priority = STATUS_PRIORITIES.get(r.get(report_flag_field, ''), 0)
                    if res_pii_priority > package_pii_priority:
                        package_pii_priority = res_pii_priority
                        package_dict[report_flag_field] = r.get(report_flag_field, '')
                        package_dict[timestamp_field] = r.get(timestamp_field, '')


    def _search_template(self):
        return render('qa_dashboard/qa_dashboard.html')
