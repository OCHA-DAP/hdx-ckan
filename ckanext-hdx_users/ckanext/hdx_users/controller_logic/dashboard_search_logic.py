import datetime

import ckan.plugins.toolkit as tk
import ckanext.hdx_search.controller_logic.search_logic as sl

_ = tk._
h = tk.h

from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER, \
    UPDATE_STATUS_UNKNOWN, UPDATE_STATUS_FRESH, UPDATE_STATUS_NEEDS_UPDATE


class DashboardSearchLogic(sl.SearchLogic):

    def __init__(self):
        super(DashboardSearchLogic, self).__init__()
        self.flask_route_name = 'hdx_user_dashboard.datasets'

    def _search_url(self, params, package_type=None):
        '''
        Returns the url of the current search type
        :param params: the parameters that will be added to the search url
        :type params: list of key-value tuples
        :param package_type: for now this is always 'dataset'
        :type package_type: string

        :rtype: string
        '''
        # url = h.url_for(self._generate_action_name(self.type), id=self.org_id)
        url = self._current_url()
        return sl.url_with_params(url, params)

    def _current_url(self):
        url = h.url_for(self.flask_route_name)
        return url

    def _add_additional_faceting_queries(self, search_data_dict):
        super(DashboardSearchLogic, self)._add_additional_faceting_queries(search_data_dict)
        now_string = datetime.datetime.utcnow().isoformat() + 'Z'
        freshness_facet_extra = 'ex={},{}'.format(UPDATE_STATUS_URL_FILTER, 'batch')
        search_data_dict.update({
            'facet.range': '{{!{extra}}}due_date'.format(extra=freshness_facet_extra),
            'f.due_date.facet.range.start': now_string + '-100YEARS',
            'f.due_date.facet.range.end': now_string + '+100YEARS',
            'f.due_date.facet.range.gap': '+100YEARS',
            'f.due_date.facet.mincount': '0',
        })
        search_data_dict.setdefault('facet.query', []).append(
            '{{!key=unknown {extra}}}-due_date:[* TO *]'.format(extra=freshness_facet_extra)
        )

    def _process_complex_facet_data(self, existing_facets, title_translations, result_facets, search_extras):
        super(DashboardSearchLogic, self)._process_complex_facet_data(existing_facets, title_translations,
                                                                      result_facets,
                                                                      search_extras)
        freshness_facet_name = 'due_date'
        if existing_facets and freshness_facet_name in existing_facets:
            item_list = existing_facets.get(freshness_facet_name).get('items')
            if item_list and len(item_list) == 2:
                item_list[0]['display_name'] = _('Needing update')
                item_list[0]['name'] = UPDATE_STATUS_NEEDS_UPDATE
                item_list[1]['display_name'] = _('Up to date')
                item_list[1]['name'] = UPDATE_STATUS_FRESH
                unknown_item = next((i for i in existing_facets.get('queries', []) if i.get('name') == 'unknown'), None)
                unknown_item['display_name'] = _('Unknown')
                unknown_item['name'] = UPDATE_STATUS_UNKNOWN
                item_list.append(unknown_item)

                title_translations[UPDATE_STATUS_URL_FILTER] = _('Update status')
                existing_facets[UPDATE_STATUS_URL_FILTER] = existing_facets[freshness_facet_name]
                del existing_facets[freshness_facet_name]
