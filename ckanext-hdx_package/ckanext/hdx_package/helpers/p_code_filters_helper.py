import ckan.plugins.toolkit as tk

config = tk.config


def are_new_p_code_filters_enabled():
    new_p_code_filters_enabled = config.get('hdx.p_code.new_filters.enabled')
    return new_p_code_filters_enabled
