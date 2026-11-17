'''
HDX-11754: check the Solr local params in the search params that CKAN core doesn't check for HDX.

HDX patches ckan/lib/search/query.py (PackageSearchQuery.run, HDX-9673) so that core's local params
check is skipped for fq, fq_list, facet.field, facet.query and facet.range, because HDX search needs
{!ex=...}, {!key=...}, {!tag=...} and {!collapse ...} there. Other local params in these params, such
as facet options or parsers like {!join}, show data from private datasets. check_hdx_local_params()
only lets through what HDX builds itself.

The check runs in HDXPackageSearchQuery.run(). The hdx_search plugin registers that class as the
package query, so every search.query_for(model.Package).run() goes through it: package_search,
package_autocomplete and HDX's direct callers. Only core's own PackageSearchQuery() calls skip it
(bulk_update_*, get_group_dataset_counts, tag_dictize); they don't set these params.

API change: these package_search requests used to reach Solr and now get a 409:
- any query parser or local param in the 5 params other than the ones listed below, e.g. {!term},
  {!prefix}, {!frange}, {!join}, {!collapse} on other fields, facet options, {!tag} in fq;
- a ${...} Solr macro in any param, including q;
- a dict or a nested list as the value of any param;
- f.<field>.facet.mincount below 1 together with a facet.field on <field>.
ckan.search.solr_allowed_query_parsers doesn't apply to the 5 params: the HDX patch has always
skipped core's check for them, and no HDX config sets it.
'''

import re
from typing import Any, Optional

import ckan.lib.search as search
from ckan.lib.search.common import SearchError
from ckan.lib.search.query import MAGIC_FIELD_RE, QUERY_PARSER_RE, PackageSearchQuery

# Local params that HDX builds itself:
#   facet.field  {!ex=groups,batch}groups              (hdx_search plugin.py, qa_search_logic.py)
#   facet.query  {!key=hxl ex=batch} vocab_Topics:hxl  (search_logic.py, qa_search_logic.py, hdx_stats.py)
#   facet.range  {!ex=ext_update_status,batch}due_date (hdx_users dashboard_search_logic.py)
#   fq_list      {!tag=groups}groups:"afg"             (search_logic.py, hdx_search plugin.py)
#                {!tag=batch q.op=OR}{!collapse field=batch nullPolicy=expand sort="last_modified desc"}
#                                                      (search_logic.py)
#                {!collapse field=organization nullPolicy=expand sort="metadata_modified desc"}
#                                                      (hdx_org_group organization_helper.py)
#   fq           none: package_search puts '+capacity:public ' in front of it, and HDX only tags fq_list
_FACET_LOCAL_PARAMS = r'\{!(?:ex|key)=[\w,.-]+(?:\s+(?:ex|key)=[\w,.-]+)*\}'
# no other local params in the rest of the value
_NO_MORE_LOCAL_PARAMS = r'(?:(?!\{!).)*'
# the batch collapse gets its sort from the search page URL, so no quotes or braces in it
_COLLAPSE = r'\{!collapse field=(?:batch|organization) nullPolicy=expand sort="[\w ,]+"\}'
_FQ_LOCAL_PARAMS = (r'(?:\{!tag=[\w,.-]+(?: q\.op=(?:AND|OR))?\})?'
                    r'(?:' + _COLLAPSE + r'|' + _NO_MORE_LOCAL_PARAMS + r')')

_ALLOWED_LOCAL_PARAMS_RE = {
    'facet.field': re.compile(_FACET_LOCAL_PARAMS + r'[\w.]+'),
    'facet.range': re.compile(_FACET_LOCAL_PARAMS + r'[\w.]+'),
    'facet.query': re.compile(_FACET_LOCAL_PARAMS + _NO_MORE_LOCAL_PARAMS, re.S),
    'fq': re.compile(_NO_MORE_LOCAL_PARAMS, re.S),
    'fq_list': re.compile(_FQ_LOCAL_PARAMS, re.S),
}

# Solr expands ${name} and ${name:default} macros before it parses a param, so a macro can build local
# params without a literal '{!', in any param, including the ones core checks
_SOLR_MACRO = '${'
_LEADING_LOCAL_PARAMS_RE = re.compile(r'^\{![^}]*\}')
_PER_FIELD_MINCOUNT_RE = re.compile(r'f\.(.+)\.facet\.mincount')


def _as_list(values: Any) -> list[Any]:
    return list(values) if isinstance(values, (list, tuple)) else [values]


def check_hdx_local_params(data_dict: dict[str, Any]) -> None:
    '''
    Raise SearchError, like core's own check (a 409 in the action API), when a param that core
    doesn't check for HDX has a magic field, or local params that HDX doesn't build itself.
    In all params: no Solr macros, and no dicts or nested lists, which core's check skips but
    core and pysolr still send to Solr (the keys of a dict, the items of a list).
    '''
    for param, values in data_dict.items():
        for value in _as_list(values):
            if isinstance(value, (dict, list, tuple, set)):
                raise SearchError(f"Values of type {type(value).__name__} are not supported in param '{param}'.")
            if isinstance(value, str) and _SOLR_MACRO in value:
                raise SearchError(f"Solr macros are not supported in param '{param}'.")

    for param, allowed_re in _ALLOWED_LOCAL_PARAMS_RE.items():
        for value in _as_list(data_dict.get(param)):
            if not isinstance(value, str):
                continue
            if MAGIC_FIELD_RE.search(value):
                raise SearchError(f"Magic fields are not supported in param '{param}'.")
            if QUERY_PARSER_RE.search(value) and not allowed_re.fullmatch(value.strip()):
                raise SearchError(f"Local parameters are not supported in param '{param}'.")

    _check_per_field_mincount(data_dict)


def _check_per_field_mincount(data_dict: dict[str, Any]) -> None:
    '''
    Core keeps facet.mincount at 1 or more, so a field facet only lists values of the datasets found.
    f.<field>.facet.mincount overrides that for one field: below 1, a facet.field on that field lists
    the values of every dataset in the index. HDX only sets it to 0 for the due_date facet.range,
    whose counts are only for the datasets found.
    '''
    facet_fields = {_LEADING_LOCAL_PARAMS_RE.sub('', value).strip()
                    for value in _as_list(data_dict.get('facet.field')) if isinstance(value, str)}
    for param, value in data_dict.items():
        match = _PER_FIELD_MINCOUNT_RE.fullmatch(param)
        if not match or match.group(1) not in facet_fields:
            continue
        try:
            mincount = int(value)
        except (TypeError, ValueError):
            mincount = 0
        if mincount < 1:
            raise SearchError(f"A value below 1 is not supported in param '{param}' "
                              f"together with a facet.field on '{match.group(1)}'.")


class HDXPackageSearchQuery(PackageSearchQuery):
    '''
    The package query that search.query_for(model.Package) returns once the hdx_search plugin is
    loaded, so that every caller of run() goes through check_hdx_local_params().
    '''

    def run(self, query: dict[str, Any], permission_labels: Optional[list[str]] = None,
            **kwargs: Any) -> dict[str, Any]:
        check_hdx_local_params(query)
        return super().run(query, permission_labels=permission_labels, **kwargs)


def register_hdx_package_search_query() -> None:
    # core has no plugin hook for the query class; query_for() reads this registry on every call.
    # test_solr_local_params.py fails if a CKAN upgrade changes that.
    search._QUERIES['package'] = HDXPackageSearchQuery
