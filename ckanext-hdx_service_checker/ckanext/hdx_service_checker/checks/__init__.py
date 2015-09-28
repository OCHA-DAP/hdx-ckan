import ckanext.hdx_service_checker.exceptions as exceptions

available_checks = {}


def add_check_implementation(name, clazz):
    available_checks[name] = clazz


def get_check_implementation(name):
    return available_checks.get(name)


class Check(object):

    def __init__(self, config):
        self.config = config
        self.name = config.get('name')
        self.subchecks = []
        if not self.name:
            raise exceptions.ParamMissingException('"name" missing from config')

    def _create_result(self):
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'result': self.result,
            'error_message': self.error_message,
            'subchecks': self.subchecks
        }

    def run_check(self):
        pass
