import logging
from datetime import datetime, timedelta

import dateutil.parser
from six import text_type

import ckan.model as model
from ckan.lib.mailer import make_key as ckan_make_key

log = logging.getLogger(__name__)


def make_key(expiration_in_minutes=24*60) -> str:
    time_part = (datetime.utcnow() + timedelta(minutes=expiration_in_minutes)).isoformat()
    random_part = text_type(ckan_make_key())
    key = '{}__{}'.format(random_part, time_part)
    return key

def create_reset_key(user, expiration_in_minutes=20):
    user.reset_key = make_key(expiration_in_minutes)
    model.repo.commit_and_remove()


class ResetKeyHelper(object):

    def __init__(self, reset_key):
        self.expiration_time = None
        key_parts = reset_key.split('__')
        if len(key_parts) == 2:
            time_part = key_parts[1]
            try:
                self.expiration_time = dateutil.parser.parse(time_part)

            except Exception as e:
                log.warning(str(e))

    def contains_expiration_time(self):
        if self.expiration_time:
            return True
        return False

    def is_expired(self):
        now_time = datetime.utcnow()
        if not self.expiration_time or now_time > self.expiration_time:
            return True
        else:
            return False
