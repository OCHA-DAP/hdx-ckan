import ckan.plugins.toolkit as tk
from ckan.types import Schema


def fix_show_schema_extras_id(schema: Schema) -> Schema:
    '''
    Make a show schema that keeps core's default_extras_schema() safe to use
    together with convert_from_extras.

    Since CKAN 2.11.6 the extras 'id' in default_extras_schema() is
    [ignore_not_sysadmin, ignore_missing, uuid_validator]. For a non-sysadmin, or
    when there is no user at all (the search index validates like that),
    ignore_not_sysadmin does data.pop(key) and raises KeyError: ('extras', N, 'id')
    when convert_from_extras has already removed that extras entry.

    We keep core's validators unchanged and only put ignore_missing in front, so an
    already removed key stops cleanly. When the id is present, core's rules apply:
    sysadmins get it validated, everyone else has it removed.

    Used by the group and organization show schemas (hdx_org_group) and by the
    showcase show schema (hdx_dataviz).

    The schema is returned unchanged when the extras have no 'id' validators (for
    example a show-style {'__extras': [keep_extras]}, which doesn't have the problem),
    when 'extras' is a plain validator list (for example [ignore_missing]), or when
    ignore_missing is already first. The last case happens because the hdx_dataviz
    showcase wrapper is applied again every time plugins are loaded.
    '''
    ignore_missing = tk.get_validator('ignore_missing')
    extras = schema.get('extras')
    id_validators = extras.get('id') if isinstance(extras, dict) else None
    if id_validators and id_validators[0] is not ignore_missing:
        extras['id'] = [ignore_missing, *id_validators]
    return schema
