import requests
import ckanext.hdx_service_checker.exceptions as exceptions

available_checks = {}


def add_check_implementation(name, clazz):
    available_checks[name] = clazz


def get_check_implementation(name):
    return available_checks.get(name)


class Check(object):

    def __init__(self, config, user_agent='SERVICE_CHECKER'):
        self.config = config
        self.user_agent = user_agent
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

    def _get_basic_header(self):
        header = {}
        if self.user_agent:
            header['User-Agent'] = self.user_agent
        return header

    def _request_get(self, url, verify=False, headers=None):
        '''
        Simple wrapper over the requests get() function. It calls self._get_basic_header() to add basic headers to
        the request.
        :param url:
        :type url: str
        :param verify:
        :type verify: bool
        :param headers:
        :type headers: dict
        :return:
        :rtype: requests.Response
        '''
        if not headers:
            headers = self._get_basic_header()
        r = requests.get(url, verify=verify, headers=headers)
        return r

    def run_check(self):
        pass
