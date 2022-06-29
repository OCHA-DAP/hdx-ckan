import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import func

import ckan.plugins.toolkit as tk

_get_action = tk.get_action


class HDXStatsHelper(object):
    IN_QA = 'in_qa'
    QA_COMPLETED = 'qa_completed'

    def __init__(self, context, compute_user_stats=True):
        super(HDXStatsHelper, self).__init__()
        self._context = context
        self._compute_user_stats = compute_user_stats

        self.active_users_completed = -1
        self.active_users_not_completed = -1

        self.orgs_total = -1
        self.orgs_with_datasets = -1
        self.orgs_updating_data_past_year = -1

        self.datasets_total = -1
        self.datasets_with_geodata = -1
        self.datasets_with_showcases = -1
        self.datasets_qa_in_quarantine = -1
        self.datasets_qa_in_qa = -1
        self.datasets_qa_qa_completed = -1

    def fetch_data(self):
        if self._compute_user_stats:
            model = self._context['model']
            self.active_users_completed = \
            model.Session.query(func.count(model.User.id)).filter(model.User.state == 'active').filter(
                model.User.fullname != None).first()[0]
            self.active_users_not_completed = model.Session.query(func.count(model.User.id)).filter(
                model.User.state == 'active').filter(model.User.fullname == None).first()[0]

        org_list = _get_action('organization_list')(self._context, {})

        self.datasets_total, facets, facet_query_map = self._general_stats_from_solr()
        self.datasets_with_geodata = facets.get('has_geodata', {}).get('true')
        self.datasets_with_showcases = facets.get('has_showcases', {}).get('true'),
        self.datasets_qa_in_quarantine = facets.get('res_extras_in_quarantine', {}).get('true', 0)
        self.datasets_qa_in_qa = facet_query_map[self.IN_QA]
        self.datasets_qa_qa_completed = facet_query_map[self.QA_COMPLETED]

        last_year_org_facets = self._last_year_stats_from_solr()

        self.orgs_total = len(org_list)
        self.orgs_with_datasets = len(facets.get('organization', {}))
        self.orgs_updating_data_past_year = len(last_year_org_facets.get('organization', {}))

        return self

    def _general_stats_from_solr(self):
        pkg_results = _get_action('package_search')(self._context, {
            'fq': '+dataset_type:dataset -extras_archived:"true"',
            'facet.field': [
                'organization',
                'has_geodata',
                'has_showcases',
                'res_extras_in_quarantine',
            ],
            "facet.query": [
                "{{!key={in_qa}}} name:[* TO *] -extras_qa_completed:true -extras_updated_by_script:[* TO *]".format(
                    in_qa=self.IN_QA),
                "{{!key={qa_completed}}} extras_qa_completed:true".format(qa_completed=self.QA_COMPLETED)
            ],
            'facet.limit': 2000,
            'q': u'',
            'rows': 1,
            'start': 0
        })
        facet_query_map = {item['name']: item['count'] for item in pkg_results['search_facets'].get('queries', [])}
        return pkg_results.get('count'), pkg_results['facets'], facet_query_map

    def _last_year_stats_from_solr(self):
        now = datetime.datetime.utcnow()
        one_year_ago = now - relativedelta(years=1)

        period_as_string = "[{}Z TO {}Z]".format(one_year_ago.isoformat(), now.isoformat())
        date_filter = " +(last_modified:{} OR review_date:{})".format(period_as_string, period_as_string)

        pkg_results = _get_action('package_search')(self._context, {
            'fq': '+dataset_type:dataset -extras_archived:"true"' + date_filter,
            'facet.field': [
                'organization',
            ],
            'facet.limit': 2000,
            'q': u'',
            'rows': 1,
            'start': 0
        })
        return pkg_results['facets']
