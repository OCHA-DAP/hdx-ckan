import ckan.plugins.toolkit as tk

config = tk.config


def are_new_cod_filters_enabled():
    new_cod_filters_enabled = config.get('hdx.cod.new_filters.enabled') == 'true'
    return new_cod_filters_enabled
