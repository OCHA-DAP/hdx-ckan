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
from ckanext.hdx_search.helpers.constants import NEW_DATASETS_FACET_NAME, UPDATED_DATASETS_FACET_NAME
from ckanext.hdx_search.helpers.qa_s3 import LogS3
from ckanext.hdx_search.helpers.solr_query_helper import generate_datetime_period_query

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

        c.full_facet_info = self._search(package_type, pager_url, use_solr_collapse=True)

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
        self._redirect_to_qa_log(resource_id, 'sdcmicro.log.txt')

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
        new_datasets_query = generate_datetime_period_query('metadata_created', 7, False)
        updated_datasets_query = generate_datetime_period_query('metadata_modified', 7, False)

        facet_queries = search_data_dict.get('facet.query') or []
        facet_queries.append('{{!key={} ex=batch}} {}'.format(NEW_DATASETS_FACET_NAME, new_datasets_query))
        facet_queries.append('{{!key={} ex=batch}} {}'.format(UPDATED_DATASETS_FACET_NAME, updated_datasets_query))
        search_data_dict['facet.query'] = facet_queries

    def _generate_facet_name_to_title_map(self, package_type):
        facets = super(HDXQAController, self)._generate_facet_name_to_title_map(package_type)
        facets['qa_completed'] = 'QA completed'
        return facets

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

            self.__add_facet_item_to_list(NEW_DATASETS_FACET_NAME, _('New datasets'), existing_facets, item_list,
                                          search_extras)
            self.__add_facet_item_to_list(UPDATED_DATASETS_FACET_NAME, _('Updated datasets'), existing_facets, item_list,
                                          search_extras)

            self.__process_qa_completed_facet(existing_facets, search_extras, item_list)

    def __add_facet_item_to_list(self, item_name, item_display_name, existing_facets, qa_only_item_list, search_extras):
        category_key = 'ext_' + item_name
        item = next(
            (i for i in existing_facets.get('queries', []) if i.get('name') == item_name), None)
        item['display_name'] = item_display_name
        item['category_key'] = category_key
        item['name'] = '1'  # this gets displayed as value in HTML <input>
        item['selected'] = search_extras.get(category_key)
        qa_only_item_list.append(item)

    def __process_qa_completed_facet(self, existing_facets, search_extras, qa_only_item_list):
        qa_completed_item = next(
            (i for i in existing_facets.get('qa_completed', {}).get('items', []) if i.get('name') == 'true'),
            None
        )
        if qa_completed_item:
            del existing_facets['qa_completed']
            qa_category_key = 'ext_qa_completed'
            qa_completed_item['category_key'] = qa_category_key
            qa_completed_item['name'] = '1'
            qa_completed_item['display_name'] = 'QA Completed'
            qa_completed_item['selected'] = search_extras.get(qa_category_key)

            qa_only_item_list.append(qa_completed_item)

    def _search_template(self):
        return render('qa_dashboard/qa_dashboard.html')
