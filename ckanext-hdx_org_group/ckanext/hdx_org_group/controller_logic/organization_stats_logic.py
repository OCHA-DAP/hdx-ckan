import logging
import itertools

import ckan.plugins.toolkit as tk

import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
import ckanext.hdx_org_group.helpers.organization_helper as helper
import ckanext.hdx_org_group.dao.common_functions as common_functions

import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_theme.util.jql as jql

log = logging.getLogger(__name__)

h = tk.h


class OrganizationStatsLogic(object):
    def __init__(self, id, user, userobj):
        super(OrganizationStatsLogic, self).__init__()
        self.org_meta_dao = org_meta_dao.OrgMetaDao(id, user, userobj)

        self.org_meta_dao.fetch_org_dict()
        self.org_meta_dao.fetch_permissions()
        self.org_meta_dao.fetch_group_message_topics()
        self.org_meta_dao.fetch_members()
        self.org_meta_dao.fetch_followers()
        helper.org_add_last_updated_field([self.org_meta_dao.org_dict])

    def is_custom(self):
        return self.org_meta_dao.is_custom

    def get_org_dict(self):
        return self.org_meta_dao.org_dict

    def fetch_stats(self):
        dw_and_pv_per_week = self._fetch_weekly_stats_from_MP()
        org_id = self.org_meta_dao.org_dict['id']
        stats_top_dataset_downloads, total_downloads_topline, stats_1_dataset_downloads_last_weeks, stats_1_dataset_name = \
            self._stats_top_dataset_downloads(org_id, self.org_meta_dao.org_dict.get('name'))

        downloaders_topline = jql.downloads_per_organization_last_30_days_cached().get(org_id, 0)
        viewers_topline = jql.pageviews_per_organization_last_30_days_cached().get(org_id, 0)

        return {
           'stats_downloaders': self._format_topline(downloaders_topline),
           'stats_viewers': self._format_topline(viewers_topline),
           'stats_top_dataset_downloads': stats_top_dataset_downloads,
           'stats_total_downloads': self._format_topline(total_downloads_topline, unit='count'),
           'stats_1_dataset_downloads_last_weeks': stats_1_dataset_downloads_last_weeks,
           'stats_1_dataset_name': stats_1_dataset_name,
           'stats_dw_and_pv_per_week': dw_and_pv_per_week
       }

    def _format_topline(self, topline_value, unit=None):
        '''
        :param topline_value:
        :type topline_value: int
        :return: dict with formatted value (as string) and unit
        :rtype: dict
        '''
        if not unit:
            unit = common_functions.compute_simplifying_units(topline_value)

        topline = [{
            'units': unit,
            'value': topline_value
        }]

        formatters.TopLineItemsFormatter(topline).format_results()
        result = topline[0]
        if result.get('units') == 'count':
            result['units'] = ''
        return result

    def _fetch_weekly_stats_from_MP(self):
        org_id = self.org_meta_dao.org_dict['id']
        pageviews_per_week_dict = jql.pageviews_per_organization_per_week_last_24_weeks_cached().get(
            org_id, {})
        downloads_per_week_dict = jql.downloads_per_organization_per_week_last_24_weeks_cached().get(
            org_id, {})

        dw_and_pv_per_week = []
        for date_str in pageviews_per_week_dict.keys():
            dw_and_pv_per_week.append({
                'org_id': org_id,
                'date': date_str,
                'pageviews': pageviews_per_week_dict[date_str].get('value', 0),
                'downloads': downloads_per_week_dict.get(date_str, {}).get('value', 0)
            })
        return dw_and_pv_per_week

    def _stats_top_dataset_downloads(self, org_id, org_name):
        from ckan.lib.search.query import make_connection
        datasets_map = jql.downloads_per_organization_per_dataset_last_24_weeks_cached().get(
            org_id, {})
        total_downloads = sum((item.get('value') for item in datasets_map.values()))

        data_dict = {
            'q': '*:*',
            'fl': 'id name title',
            'fq': 'capacity:"public" organization:{}'.format(org_name),
            'rows': 5000, # Just setting a max, we need all public datasets that an org has
            'start': 0,
        }

        ret = []
        if datasets_map:
            mp_datasets_sorted = sorted(datasets_map.values(), key=lambda item: item.get('value'), reverse=True)
            try:
                conn = make_connection(decode_dates=False)
                search_result = conn.search(**data_dict)
                dataseta_meta_map = {
                    d['id']: {
                        'title': d.get('title'),
                        'name': d.get('name'),
                    }
                    for d in search_result.docs
                }
                ret = [
                    {
                        'dataset_id': d.get('dataset_id'),
                        'name': dataseta_meta_map.get(d.get('dataset_id'), {}).get('title'),
                        'url': h.url_for('dataset_read', id=dataseta_meta_map.get(d.get('dataset_id'), {}).get('name')),
                        'value': d.get('value'),
                        'total': total_downloads,
                        # 'percentage': round(100*d.get('value', 0)/total_downloads, 1)
                    }
                    for d in itertools.islice(
                        (ds for ds in mp_datasets_sorted if ds.get('dataset_id') in dataseta_meta_map), 25
                    )
                ]
            except Exception as e:
                log.warn('Error in searching solr {}'.format(str(e)))

        # query = get_action('package_search')(context, data_dict)
        stats_1_dataset_downloads_last_weeks = []
        stats_1_dataset_name = None
        if ret and len(ret) == 1:
            dataset_id = ret[0].get('dataset_id')
            stats_1_dataset_downloads_last_weeks = \
                list(jql.fetch_downloads_per_week_for_dataset(dataset_id).values())
            stats_1_dataset_name = ret[0].get('name')

        return ret, total_downloads, stats_1_dataset_downloads_last_weeks, stats_1_dataset_name
