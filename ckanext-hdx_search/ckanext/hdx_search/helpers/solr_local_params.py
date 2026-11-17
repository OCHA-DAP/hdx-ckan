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
(bulk_update_*, get_group_dataset_counts, tag_dictize); they set fq and facet.field only to fixed
values, never from the request.

API change: these package_search requests used to reach Solr and now get a 409:
- any query parser or local param in the 5 params other than the ones listed below, e.g. {!term},
  {!prefix}, {!frange}, {!join}, {!collapse} on other fields, facet options, {!tag} in fq;
- a ${...} Solr macro or a unicode escape (\\u005f) in any param, including q;
- a dict or a nested list as the value of any param;
- f.<field>.facet.mincount below 1, or not a whole number, together with a facet.field on <field>.
Params that core doesn't accept still get core's 400 'Invalid search parameters'.
The search page shows its search error state for these, and logs them as warnings, not errors.
ckan.search.solr_allowed_query_parsers doesn't apply to the 5 params: the HDX patch has always
skipped core's check for them, and no HDX config sets it.
'''

import re
from typing import Any, Optional

import ckan.lib.search as search
from ckan.lib.search.common import SearchError
from ckan.lib.search.query import MAGIC_FIELD_RE, QUERY_PARSER_RE, VALID_SOLR_PARAMETERS, PackageSearchQuery

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
# Solr's query parser turns \uXXXX into its character before it reads field names and quoted text, so
# _query_ is the _query_ magic field, which MAGIC_FIELD_RE doesn't see. It does see a backslash
# escape (\_query\_), and an escaped \{! only gets parsed inside the quoted text of a magic field.
_UNICODE_ESCAPE_RE = re.compile(r'\\u[0-9a-fA-F]{4}')
_LEADING_LOCAL_PARAMS_RE = re.compile(r'^\{![^}]*\}')
_PER_FIELD_MINCOUNT_RE = re.compile(r'f\.(.+)\.facet\.mincount')
# what Solr reads as an int (Java's Integer.parseInt): no spaces, decimals or non-ASCII digits
_WHOLE_NUMBER_RE = re.compile(r'[+-]?[0-9]+')


class UnsupportedSearchParamError(SearchError):
    '''
    A search param that HDX doesn't accept. It is a SearchError, so the action API still returns a 409,
    and the search page can tell it apart from Solr errors.
    '''


def _as_list(values: Any) -> list[Any]:
    return list(values) if isinstance(values, (list, tuple)) else [values]


def check_hdx_local_params(data_dict: dict[str, Any]) -> None:
    '''
    Raise UnsupportedSearchParamError, a SearchError like core's own check (a 409 in the action
    API), when a param that core doesn't check for HDX has a magic field, or local params that HDX
    doesn't build itself. In all params: no Solr macros or unicode escapes, and no dicts or nested
    lists, which core's check skips but core and pysolr still send to Solr (the keys of a dict, the
    items of a list).
    Params that core doesn't accept are left to core, which rejects them before anything reaches Solr.
    '''
    solr_params = {param: values for param, values in data_dict.items() if param in VALID_SOLR_PARAMETERS}
    for param, values in solr_params.items():
        allowed_re = _ALLOWED_LOCAL_PARAMS_RE.get(param)
        for value in _as_list(values):
            if isinstance(value, (dict, list, tuple, set)):
                raise UnsupportedSearchParamError(
                    f"Values of type {type(value).__name__} are not supported in param '{param}'.")
            if not isinstance(value, str):
                continue
            if _SOLR_MACRO in value:
                raise UnsupportedSearchParamError(f"Solr macros are not supported in param '{param}'.")
            if _UNICODE_ESCAPE_RE.search(value):
                raise UnsupportedSearchParamError(f"Unicode escapes are not supported in param '{param}'.")
            if allowed_re is None:
                continue
            if MAGIC_FIELD_RE.search(value):
                raise UnsupportedSearchParamError(f"Magic fields are not supported in param '{param}'.")
            if QUERY_PARSER_RE.search(value) and not allowed_re.fullmatch(value.strip()):
                raise UnsupportedSearchParamError(f"Local parameters are not supported in param '{param}'.")

    _check_per_field_mincount(solr_params)


def _check_per_field_mincount(solr_params: dict[str, Any]) -> None:
    '''
    Core keeps facet.mincount at 1 or more, so a field facet only lists values of the datasets found.
    f.<field>.facet.mincount overrides that for one field: below 1, a facet.field on that field lists
    the values of every dataset in the index. HDX only sets it to 0 for the due_date facet.range,
    whose counts are only for the datasets found.
    '''
    facet_fields = {_LEADING_LOCAL_PARAMS_RE.sub('', value).strip()
                    for value in _as_list(solr_params.get('facet.field')) if isinstance(value, str)}
    for param, values in solr_params.items():
        match = _PER_FIELD_MINCOUNT_RE.fullmatch(param)
        if not match or match.group(1) not in facet_fields:
            continue
        for value in _as_list(values):
            # str() of a bool or a float doesn't match, so True and 1.5 aren't read as 1
            if not _WHOLE_NUMBER_RE.fullmatch(str(value)):
                raise UnsupportedSearchParamError(
                    f"Values that are not whole numbers are not supported in param '{param}'.")
            if int(value) < 1:
                raise UnsupportedSearchParamError(f"A value below 1 is not supported in param '{param}' "
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
