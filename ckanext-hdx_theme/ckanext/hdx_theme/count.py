import json
from ckan import model
from ckan.lib import base
import sqlalchemy

class CountController(base.BaseController):

    def _get_count(self, table, type):
        q = sqlalchemy.text(''' select count(*) from {name} where state='active' and type='{type}';'''.format(name=table, type=type))
        result = model.Session.connection().execute(q, entity_id=id).scalar()
        return result

    def dataset(self):
        return json.dumps({'count': self._get_count('package', 'dataset')})

    def country(self):
        return json.dumps({'count': self._get_count('"group"', 'group')})

    def source(self):
        return json.dumps({'count': 0})