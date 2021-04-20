import logging

import ckan.logic as logic
import ckan.plugins.toolkit as tk

import ckanext.hdx_service_checker.checker as checker
import ckanext.hdx_service_checker.exceptions as exceptions

log = logging.getLogger(__name__)
config = tk.config


@logic.side_effect_free
def run_checks(context, data_dict):
    logic.check_access('run_checks', context, data_dict)
    config_file_path = config.get('hdx.checks.config_path')
    if config_file_path:
        result = checker.run_checks(config_file_path, config)
        return result
    else:
        log.error("'hdx.checks.config_path' missing from ckan config")
        raise exceptions.ParamMissingException("'hdx.checks.config_path' missing from ckan config")
