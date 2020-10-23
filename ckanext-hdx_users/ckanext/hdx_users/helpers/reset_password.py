import logging
from datetime import datetime, timedelta

import dateutil.parser
from six import text_type

import ckan.model as model
from ckan.lib.mailer import make_key

log = logging.getLogger(__name__)


def create_reset_key(user, expiration_in_hours=3):
    time_part = (datetime.utcnow() + timedelta(hours=expiration_in_hours)).isoformat()
    random_part = text_type(make_key())
    user.reset_key = '{}__{}'.format(random_part, time_part)
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
