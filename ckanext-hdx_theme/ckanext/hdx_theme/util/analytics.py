import logging
import json
import requests

import pylons.config as config


from ckan.common import _, request

log = logging.getLogger(__name__)

class AbstractAnalyticsSender(object):

    def __init__(self):
        self.analytics_enqueue_url = config.get('hdx.analytics.enqueue_url')
        self.analytics_dict = None
        self.response = None

        self.referer_url = request.referer
        self.remote_addr = request.remote_addr
        self.request_url = request.url

    def send_to_queue(self):
        try:
            if self.analytics_dict:
                self._populate_defaults()

                self.response = requests.post(self.analytics_enqueue_url, allow_redirects=True, timeout=2,
                                              data=json.dumps(self.analytics_dict),
                                              headers={'Content-type': 'application/json'})

                self.response.raise_for_status()
                enq_result = self.response.json()
                log.info('Enqueuing result was: {}'.format(enq_result.get('success')))

            else:
                log.error('The analytics dict is empty. Can\'t send it to the queue')

        except requests.ConnectionError, e:
            log.error("There was a connection error to the analytics enqueuing service: {}".format(str(e)))
        except requests.HTTPError, e:
            log.error("Bad HTTP response from analytics enqueuing service: {}".format(str(e)))
        except requests.Timeout, e:
            log.error("Request timed out: {}".format(str(e)))
        except Exception, e:
            log.error('Unexpected error {}'.format(e))

    def _populate_defaults(self):
        self._set_if_not_exists(self.analytics_dict, 'mixpanel_tracking_id', 'anonymous')
        self._set_if_not_exists(self.analytics_dict, 'mixpanel_token', config.get('hdx.analytics.mixpanel.token'))
        self._set_if_not_exists(self.analytics_dict, 'send_mixpanel', True)
        self._set_if_not_exists(self.analytics_dict, 'send_ga', False)

        mixpanel_meta = self.analytics_dict.get('mixpanel_meta')
        self._set_if_not_exists(mixpanel_meta, 'server side', True)
        self._set_if_not_exists(mixpanel_meta, 'referer url', self.referer_url)

        ga_meta = self.analytics_dict.get('ga_meta')
        self._set_if_not_exists(ga_meta, 'uip', self.remote_addr)
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
