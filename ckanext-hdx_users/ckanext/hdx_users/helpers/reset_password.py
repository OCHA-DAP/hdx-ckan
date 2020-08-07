from datetime import datetime, timedelta

from six import text_type

import ckan.model as model
from ckan.lib.mailer import make_key


def create_reset_key(user, expiration_in_hours=3):
  time_part = (datetime.utcnow() + timedelta(hours=expiration_in_hours)).isoformat()
  random_part = text_type(make_key())
  user.reset_key = '{}__{}'.format(random_part, time_part)
  model.repo.commit_and_remove()
