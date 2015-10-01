
import importlib
import threading
import logging
import json
import re

import ckanext.hdx_service_checker.checks as checks
import ckanext.hdx_service_checker.exceptions as exceptions

log = logging.getLogger(__name__)

LOCK = threading.RLock()


def run_checks(config_file_path, runtime_vars):
    with open(config_file_path) as file_data:
        config_list = json.load(file_data)
    if config_list:
        checker = Checker(config_list, runtime_vars)
        return checker.run_checks()
    else:
        raise exceptions.ParamMissingException("Missing config for file path")


class Checker(object):
    def __init__(self, config_list, runtime_vars):
        self.checks = []
        for config in config_list:
            class_name = config['class_name']
            module_name = config['module_name']
            key = '{}:{}'.format(module_name, class_name)

            self.__replace_runtime_vars(config, runtime_vars)

            # 2 or more requests could hit this at the same time
            with LOCK:
                if not checks.get_check_implementation(key):
                    c_module = importlib.import_module(module_name)
                    clazz = getattr(c_module, class_name)
                    checks.add_check_implementation(key, clazz)

            check_obj = checks.get_check_implementation(key)(config)
            self.checks.append(check_obj)
        pass

    def __replace_runtime_vars(self, config, runtime_vars):
        '''
        Replaces runtime variables in the configuration. Config dict is modified.
        :param config: configuration for 1 check
        :type config: dict
        :param runtime_vars: variables determined at application runtime
        :type runtime_vars: dict
        '''
        def __replace_var(match):
            var_name = match.group(1)
            var_value = runtime_vars.get(var_name)
            if not var_value:
                raise exceptions.ParamMissingException('{} is not a runtime variable'.format(var_name))
            else:
                return str(var_value)

        for key in config.keys():
            val = config.get(key)
            if val:
                new_val = re.sub(r'\#\{([a-zA-Z0-9-_.]+)\}', __replace_var, str(val))
                config[key] = new_val

    def run_checks(self):
        result_list = []
        for check in self.checks:
            log.debug('Running check: {}'.format(str(check.config)))
            result = check.run_check()
            result_list.append(result)
            log.info(str(result))

        return result_list

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p', handlers=[logging.StreamHandler()])
    runtime_vars = {
        'hdx.rest.indicator.endpoint': 'https://manage.hdx.rwlabs.org/public/api2/values',
        'SOLR_URL': 'http://172.17.42.1:9011/solr/ckan/select?q=health&start=0&rows=1'
    }
    config_file = '/home/alex/PycharmProjects/hdx-ckan/ckanext-hdx_service_checker/ckanext/hdx_service_checker/config/config.json'
    run_checks(config_file, runtime_vars)
