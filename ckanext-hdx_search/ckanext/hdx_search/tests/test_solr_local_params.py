"""
HDX-11754: package_search only accepts the Solr local params that HDX builds itself.

HDX patches CKAN core (ckan/lib/search/query.py, HDX-9673) so that core's local params check
is skipped for fq, fq_list, facet.field, facet.query and facet.range, because HDX search needs
{!ex=...}, {!key=...}, {!tag=...} and {!collapse ...} in them. Without any check, all local
params in these 5 params reach Solr: facet options that list the names of private datasets,
or parsers like {!join} that tell whether a private dataset matches a query. CKAN 2.11.6 and
2.11.7 fixed these in core's check (GHSA-5r6j-4c43-7mx6, GHSA-xj2r-hpg6-375c), which the HDX
patch skips.

All searches run as an anonymous user, through the action API (a 409 for a SearchError, the same
as core's check) or the search page.
"""

from unittest import mock

import pytest

import ckan.lib.search as search
import ckan.model as model
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs
from ckan.lib.search.common import SearchError, SearchQueryError
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER
import ckanext.hdx_search.controller_logic.search_logic as search_logic
from ckanext.hdx_search.helpers.solr_local_params import (
    HDXPackageSearchQuery,
    UnsupportedSearchParamError,
    check_hdx_local_params,
)
from ckanext.hdx_search.helpers.constants import (
    ARCHIVED_DATASETS_FACET_NAME,
    DEFAULT_SORTING,
    HPC_DATASETS_FACET_QUERY,
    HXLATED_DATASETS_FACET_QUERY,
)

PRIVATE_DATASET = 'test_private_dataset_1'
PUBLIC_ORG_DATASETS = ('test_dataset_1', 'test_indicator_1', 'test_indicator_2')

# matches only the private dataset; the public datasets are in the same organization
PRIVATE_MATCH = 'name:test_private*'
JOIN_ON_PRIVATE = '{!join from=organization to=organization}' + PRIVATE_MATCH
# Solr reads _ as '_' in a field name and \{ as '{' in quoted text: the join above in the _query_
# magic field, without a literal '_query_' or '{!'
ESCAPED_JOIN_ON_PRIVATE = '+\\u005fquery\\u005f:"\\' + JOIN_ON_PRIVATE + '"'

# Same format as the batch collapse filter in search_logic.py, which gets the sort from the URL.
# The search page also sends that sort as Solr's sort, which core checks, so a quote in it is only
# tested here through the API's fq_list.
COLLAPSE_BATCH_FQ = '{{!tag=batch q.op=OR}}{{!collapse field=batch nullPolicy=expand sort="{sort}"}} '
INJECTED_SORT = DEFAULT_SORTING + '"} +{!join from=organization to=organization v="' + PRIVATE_MATCH

# params that package_search takes as a list
LIST_PARAMS = ('facet.field', 'facet.query', 'fq_list')

# Local params that HDX doesn't build. All of them are valid for Solr, so a search with any of
# them succeeds while nothing checks these params.
REJECTED_CASES = [
    pytest.param('facet.field', '{!facet.mincount=0 facet.prefix=test_private key=leak}name',
                 id='facet.field-facet-options'),
    pytest.param('facet.field', '{!ex=batch facet.mincount=0}name',
                 id='facet.field-hdx-ex-plus-facet-option'),
    pytest.param('facet.range',
                 '{!facet.range.start=NOW-1YEAR facet.range.end=NOW facet.range.gap=+1YEAR}metadata_created',
                 id='facet.range-facet-options'),
    pytest.param('facet.query', '{!join from=organization to=organization key=leak}' + PRIVATE_MATCH,
                 id='facet.query-join'),
    pytest.param('facet.query', '{!key=leak}_query_:"' + JOIN_ON_PRIVATE + '"',
                 id='facet.query-hdx-key-plus-magic-field'),
    pytest.param('fq', JOIN_ON_PRIVATE, id='fq-join'),
    pytest.param('fq', '_query_:"' + JOIN_ON_PRIVATE + '"', id='fq-magic-field'),
    pytest.param('fq_list', JOIN_ON_PRIVATE, id='fq_list-join'),
    pytest.param('fq_list', '{!tag=groups}groups:roger ' + JOIN_ON_PRIVATE, id='fq_list-hdx-tag-plus-join'),
    pytest.param('fq_list', COLLAPSE_BATCH_FQ.format(sort=INJECTED_SORT), id='fq_list-collapse-injected-sort'),
    # Solr expands the macro to '{!' before it parses the value
    pytest.param('fq_list', '{${zz:!}join from=organization to=organization}' + PRIVATE_MATCH, id='fq_list-macro'),
    pytest.param('facet.field', '{${zz:!}facet.mincount=0 facet.prefix=test_private key=leak}name',
                 id='facet.field-macro'),
    pytest.param('fq', ESCAPED_JOIN_ON_PRIVATE, id='fq-unicode-escape'),
    pytest.param('fq_list', ESCAPED_JOIN_ON_PRIVATE, id='fq_list-unicode-escape'),
    pytest.param('facet.query', ESCAPED_JOIN_ON_PRIVATE, id='facet.query-unicode-escape'),
]

# Searches that get around a check that only looks at text values or at '{!'
REJECTED_SEARCHES = [
    # core and pysolr send the keys of a dict, and the items of a nested list, to Solr
    pytest.param({'fq_list': {JOIN_ON_PRIVATE: 1}}, id='fq_list-dict'),
    pytest.param({'facet.query': {'{!key=leak}' + PRIVATE_MATCH: 1}}, id='facet.query-dict'),
    pytest.param({'fq_list': [[JOIN_ON_PRIVATE]]}, id='fq_list-nested-list'),
    # core checks q itself, but only for a literal '{!'
    pytest.param({'q': '{${zz:!}join from=organization to=organization}' + PRIVATE_MATCH}, id='q-macro'),
    # with include_private, fq has nothing in front of it: a tag on it would also tag the state filter
    pytest.param({'fq': '{!tag=leak}*:*', 'include_private': True}, id='fq-tag-include-private'),
    # a field facet with mincount 0 lists the values of every dataset in the index
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': '0'}, id='facet.field-mincount-0'),
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': 'abc'},
                 id='facet.field-mincount-not-a-number'),
    # int() reads these as 1 or 10, but Solr doesn't
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': 1.5}, id='facet.field-mincount-float'),
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': True}, id='facet.field-mincount-bool'),
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': '1_0'},
                 id='facet.field-mincount-underscore'),
    pytest.param({'facet.field': ['due_date'], 'f.due_date.facet.mincount': ['0']}, id='facet.field-mincount-list'),
    # core checks q itself, but its magic field check doesn't see unicode escapes
    pytest.param({'q': ESCAPED_JOIN_ON_PRIVATE}, id='q-unicode-escape'),
]

# Local params that HDX builds itself. These searches must keep working.
ACCEPTED_CASES = [
    # facet.field: search page and QA dashboard (hdx_search plugin.py, search_logic.py, qa_search_logic.py)
    pytest.param({'facet.field': [
        '{!ex=groups,batch}groups',
        '{!ex=batch}site_id',
        '{!ex=batch,archived}extras_archived',
        '{!ex=cod_level,batch}cod_level',
        '{!ex=methodology,batch}methodology',
    ]}, id='facet.field-ex'),
    # facet.query: search page, QA dashboard, dataset dashboard and stats
    # (search_logic.py, qa_search_logic.py, hdx_users dashboard_search_logic.py, hdx_theme hdx_stats.py)
    pytest.param({'facet.query': [
        '{{!key=hxl ex=batch}} {}'.format(HXLATED_DATASETS_FACET_QUERY),
        '{{!key=hpc ex=vocab_Topics,batch}} {}'.format(HPC_DATASETS_FACET_QUERY),
        '{!key=new_datasets ex=batch} metadata_created:[NOW-7DAYS TO NOW]',
        '{{!key=unknown ex={},batch}}-due_date:[* TO *]'.format(UPDATE_STATUS_URL_FILTER),
        '{!key=in_qa} name:[* TO *] -extras_qa_completed:true -extras_updated_by_script:[* TO *]',
    ]}, id='facet.query-key-ex'),
    # facet.range: freshness on the dataset dashboard (hdx_users dashboard_search_logic.py)
    pytest.param({
        'facet.range': '{{!ex={},batch}}due_date'.format(UPDATE_STATUS_URL_FILTER),
        'f.due_date.facet.range.start': 'NOW-100YEARS',
        'f.due_date.facet.range.end': 'NOW+100YEARS',
        'f.due_date.facet.range.gap': '+100YEARS',
        'f.due_date.facet.mincount': '0',
    }, id='facet.range-ex'),
    # fq_list: search page filters and the freshness filter (search_logic.py, plugin.py)
    pytest.param({'fq_list': [
        '{!tag=groups}groups:"roger"',
        '{{!tag={}}}-extras_archived:"true"'.format(ARCHIVED_DATASETS_FACET_NAME),
        '{{!tag={}}}due_date: [* TO NOW] OR (*:* -due_date: [* TO *])'.format(UPDATE_STATUS_URL_FILTER),
    ]}, id='fq_list-tag'),
    # fq_list: batch collapse on the search page (search_logic.py), with the sort values the UI uses
    pytest.param({'fq_list': [COLLAPSE_BATCH_FQ.format(sort=DEFAULT_SORTING)], 'expand': 'true'},
                 id='fq_list-collapse-batch'),
    pytest.param({'fq_list': [COLLAPSE_BATCH_FQ.format(sort='score desc, ' + DEFAULT_SORTING)], 'expand': 'true'},
                 id='fq_list-collapse-batch-score-sort'),
    pytest.param({'fq_list': [COLLAPSE_BATCH_FQ.format(sort='title_case_insensitive asc')], 'expand': 'true'},
                 id='fq_list-collapse-batch-title-sort'),
    # fq_list: last update of each organization (hdx_org_group organization_helper.py)
    pytest.param({'fq_list': ['{!collapse field=organization nullPolicy=expand sort="metadata_modified desc"} ']},
                 id='fq_list-collapse-organization'),
    # fq: no local params, only the braces of an exclusive range
    pytest.param({'fq': '+metadata_modified:{2000-01-01T00:00:00Z TO *}'}, id='fq-exclusive-range'),
]


def _summary(res):
    '''Short failure message: the parts of the response that matter here, not the whole body.'''
    data = res.get_json(silent=True) or {}
    result = data.get('result') or {}
    summary = {
        'error': data.get('error'),
        'count': result.get('count'),
        'facets': result.get('facets'),
        'facet_queries': result.get('facet_queries'),
    }
    return 'HTTP {} {}'.format(res.status_code, {k: v for k, v in summary.items() if v})[:600]


class TestSolrLocalParams(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def _anonymous_search(self, data_dict):
        return self.app.post('/api/action/package_search', json=data_dict)

    def _assert_rejected(self, res):
        assert res.status_code == 409, _summary(res)
        assert 'not supported in param' in res.json['error']['message'], _summary(res)

    def test_facet_field_does_not_list_private_dataset_names(self):
        res = self._anonymous_search({
            'q': 'name:zzz-no-match',
            'facet.field': ['{!facet.mincount=0 facet.prefix=test_private key=leak}name'],
        })

        assert PRIVATE_DATASET not in res.get_data(as_text=True), _summary(res)
        self._assert_rejected(res)

    @pytest.mark.parametrize('param, value', REJECTED_CASES)
    def test_rejects_local_params_hdx_does_not_build(self, param, value):
        res = self._anonymous_search({param: [value] if param in LIST_PARAMS else value})

        self._assert_rejected(res)

    @pytest.mark.parametrize('data_dict', REJECTED_SEARCHES)
    def test_rejects_searches_around_the_check(self, data_dict):
        self._assert_rejected(self._anonymous_search(data_dict))

    def test_every_package_query_checks_local_params(self):
        # Not only package_search: query_for(model.Package) has direct callers (hdx_theme
        # helpers/actions.py, core's package_autocomplete). This also fails if a CKAN upgrade
        # changes the registry that the hdx_search plugin puts the HDX query class in.
        query = search.query_for(model.Package)

        assert isinstance(query, HDXPackageSearchQuery)
        with pytest.raises(UnsupportedSearchParamError, match='not supported in param'):
            query.run({'q': '*:*', 'fq_list': [JOIN_ON_PRIVATE]}, permission_labels=['public'])

    def test_leaves_unknown_params_to_core(self):
        # core rejects params it doesn't accept with a 400, before anything reaches Solr
        res = self._anonymous_search({'foo': '${x}', 'bar': {'a': 1}})

        assert res.status_code == 400, _summary(res)
        assert 'Invalid search parameters' in res.json['error']['message'], _summary(res)
        with pytest.raises(SearchQueryError, match='Invalid search parameters'):
            search.query_for(model.Package).run({1: 'x'})

    @pytest.mark.parametrize('mincount', [1, '2', '+3', ['4']])
    def test_accepts_whole_number_mincount_of_1_or_more(self, mincount):
        # only the check: Solr can't facet on due_date, the only field core takes a mincount for
        check_hdx_local_params({'facet.field': ['due_date'], 'f.due_date.facet.mincount': mincount})

    @pytest.mark.parametrize('data_dict', ACCEPTED_CASES)
    def test_accepts_local_params_hdx_builds(self, data_dict):
        res = self._anonymous_search(data_dict)

        assert res.status_code == 200, _summary(res)
        assert res.json['success'] is True

    def _search_page_lists_org_datasets(self, params):
        res = self.app.get('/search', query_string=params)
        assert res.status_code == 200
        body = res.get_data(as_text=True)
        return any('/dataset/{}"'.format(name) in body for name in PUBLIC_ORG_DATASETS)

    def test_search_page_lists_org_datasets(self):
        # makes sure the check below would see the datasets if the page listed them
        assert self._search_page_lists_org_datasets({})

    def test_search_page_fq_cannot_add_local_params(self):
        # The search page adds the fq URL argument to the filter. Without the check, a join there
        # lists the public datasets of the private dataset's organization only when the private
        # dataset matches. With it, the page shows its search error state, with no datasets.
        assert not self._search_page_lists_org_datasets({'fq': JOIN_ON_PRIVATE})

    def test_search_page_fq_cannot_use_unicode_escapes(self):
        assert not self._search_page_lists_org_datasets({'fq': ESCAPED_JOIN_ON_PRIVATE})

    def test_search_page_shows_search_error_instead_of_500(self):
        # core's check rejects local params in sort; the page used to fail building its pagination
        assert not self._search_page_lists_org_datasets({'sort': INJECTED_SORT})

    def _search_page_log_levels(self, monkeypatch, params):
        # the module's logger, not caplog: the test ini's logging config disables loggers created before it
        log = mock.Mock()
        monkeypatch.setattr(search_logic, 'log', log)
        assert not self._search_page_lists_org_datasets(params)
        return [name for name, args, _ in log.method_calls if args and str(args[0]).startswith('Dataset search')]

    @pytest.mark.parametrize('params', [
        pytest.param({'fq': JOIN_ON_PRIVATE}, id='hdx-check'),
        # Solr can't parse a sort without a direction; core raises a SearchQueryError for that
        pytest.param({'sort': 'metadata_modified'}, id='core-invalid-sort'),
    ])
    def test_search_page_logs_rejected_searches_as_warnings(self, monkeypatch, params):
        # bots crawl the search page: searches that the request breaks don't go to the error log
        assert self._search_page_log_levels(monkeypatch, params) == ['warning']

    def test_search_page_logs_solr_errors_as_errors(self, monkeypatch):
        def _solr_error(*args, **kwargs):
            raise SearchError('SOLR returned an error running query')
        monkeypatch.setattr(search_logic.SearchLogic, '_performing_search', _solr_error)

        assert self._search_page_log_levels(monkeypatch, {}) == ['error']
