import json
import logging
import time
import six
from six.moves.urllib.parse import urlparse

import ipaddress
import requests
import ua_parser.user_agent_parser as useragent

import ckan.plugins.toolkit as tk
from ckanext.hdx_theme.helpers.hash_generator import HashCodeGenerator

log = logging.getLogger(__name__)

request = tk.request
config = tk.config


class AbstractAnalyticsSender(object):

    def __init__(self):
        self.analytics_enqueue_url = config.get('hdx.analytics.enqueue_url')
        self.analytics_dict = None
        self.response = None

        self.pushed_successfully = False

        try:
            self.referer_url = request.referrer
            self.user_addr = request.environ.get('HTTP_X_REAL_IP')
            self.__check_ip_addr_public()
            self.request_url = request.url

            ua = request.user_agent if request.user_agent is not None else ''
            self.user_agent = ua if isinstance(ua, six.string_types) else ua.string
            ua_dict = useragent.Parse(self.user_agent)

            self.is_api_call = False
            rq_headers = request.headers if request.headers else request._headers
            if rq_headers and rq_headers.environ:
                self.is_api_call = self.is_ckan_api_call(rq_headers.environ)

            if not self.user_agent or not self.user_agent.strip():
                log.warning('User agent is empty for IP address {}'.format(self.user_addr))

            if ua_dict:
                self.ua_browser = ua_dict.get('user_agent', {}).get('family')
                self.ua_browser_version = ua_dict.get('user_agent', {}).get('major')
                self.ua_os = ua_dict.get('os', {}).get('family')

            else:
                log.error('User agent could not be parsed for {}'.format(request.user_agent))

        except Exception as e:
            log.warning('request specific info could not be found. This is normal for nose tests. Exception is {}'.format(
                str(e)))

    def send_to_queue(self):
        try:
            if self.analytics_enqueue_url:
                if self.analytics_dict:
                    self._populate_defaults()

                    self.response = self._make_http_call()
                    enq_result = self.response.json()
                    log.info('Enqueuing result was: {}'.format(enq_result.get('success')))
                    self.pushed_successfully = True
                else:
                    log.error('The analytics dict is empty. Can\'t send it to the queue')
            else:
                log.warning('Analytics enqueque url is empty so event was NOT put in queue. This is normal for tests !')

        except requests.ConnectionError as e:
            log.error("There was a connection error to the analytics enqueuing service: {}".format(str(e)))
        except requests.HTTPError as e:
            log.error("Bad HTTP response from analytics enqueuing service: {}".format(str(e)))
        except requests.Timeout as e:
            log.error("Request timed out: {}".format(str(e)))
        except Exception as e:
            log.error('Unexpected error {}'.format(e))

    def _make_http_call(self):
        response = requests.post(self.analytics_enqueue_url, allow_redirects=True, timeout=2,
                                      data=json.dumps(self.analytics_dict),
                                      headers={'Content-type': 'application/json'})
        response.raise_for_status()
        return response

    def __check_ip_addr_public(self):
        if self.user_addr:
            user_address = self.user_addr.split(',')[0]
            ip_addr = ipaddress.ip_address(six.text_type(user_address))
            if ip_addr.is_private:
                log.warn('IP address used in analytics event {} is not public.'
                         'This could be normal for tests and dev env.'.format(self.__class__.__name__))

    def _populate_defaults(self):

        # computing distinct id based on ip and UA
        distinct_id = HashCodeGenerator({'ip': self.user_addr, 'ua': self.user_agent}).compute_hash()
        # this is the mixpanel distinct_id
        self._set_if_not_exists(self.analytics_dict, 'mixpanel_tracking_id', distinct_id)

        self._set_if_not_exists(self.analytics_dict, 'mixpanel_token', config.get('hdx.analytics.mixpanel.token'))
        self._set_if_not_exists(self.analytics_dict, 'send_mixpanel', True)
        self._set_if_not_exists(self.analytics_dict, 'send_ga', False)

        mixpanel_meta = self.analytics_dict.get('mixpanel_meta')
        if self.is_api_call:
            self._set_if_not_exists(mixpanel_meta, 'event source', 'api')

        # setting the event time
        event_time = time.time()
        self._set_if_not_exists(mixpanel_meta, 'time', event_time)

        self._set_if_not_exists(mixpanel_meta, 'server side', True)
        self._set_if_not_exists(mixpanel_meta, 'user agent', self.user_agent)
        self._set_if_not_exists(mixpanel_meta, 'referer url', self.referer_url)
        self._set_if_not_exists(mixpanel_meta, 'ip', self.user_addr)
        self._set_if_not_exists(mixpanel_meta, '$os', self.ua_os)
        self._set_if_not_exists(mixpanel_meta, '$browser', self.ua_browser)
        self._set_if_not_exists(mixpanel_meta, '$browser_version', self.ua_browser_version)
        self._set_if_not_exists(mixpanel_meta, '$current_url', self.request_url)

        ga_meta = self.analytics_dict.get('ga_meta')
        self._set_if_not_exists(ga_meta, 'uip', self.user_addr)
        self._set_if_not_exists(ga_meta, 'dl', self.request_url)
        self._set_if_not_exists(ga_meta, 'ds', 'direct')
        self._set_if_not_exists(ga_meta, 'v', '1')
        self._set_if_not_exists(ga_meta, 't', 'event')
        self._set_if_not_exists(ga_meta, 'cid', 'anonymous')
        self._set_if_not_exists(ga_meta, 'tid', config.get('hdx.analytics.ga.token'))

    @staticmethod
    def _set_if_not_exists(data_dict, key, value):
        if not data_dict.get(key):
            data_dict[key] = value

    @staticmethod
    def is_ckan_api_call(environ):
        url_path = AbstractAnalyticsSender._get_current_path(environ)
        if url_path:
            return '/api/' in url_path and '/action/' in url_path
        return False

    @staticmethod
    def _get_current_path(environ):
        url = environ.get('CKAN_CURRENT_URL')
        try:
            called_url = urlparse(url)
            return called_url.path
        except Exception as e:
            log.error('Exception while trying get current url', six.text_type(e))

        return None

