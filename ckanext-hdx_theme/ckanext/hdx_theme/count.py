import json
from ckan import model
from ckan.lib import base
import sqlalchemy


class CountController(base.BaseController):


    def _get_count(self, table, type, extra):
        isPrivate=''
        extraQ=''
        if type == 'dataset':
            isPrivate=' and private = FALSE';

        if extra:
            extraQ = "where state='active' and type='{type}' {isPrivate}".format(type=type, isPrivate=isPrivate)

        q = sqlalchemy.text(''' select count(*) from {name} {extra};'''.format(name=table, extra=extraQ))
        result = model.Session.connection().execute(q, entity_id=id).scalar()
        return result

    def dataset(self):
        return json.dumps({'count': self._get_count('package', 'dataset', True)})

    def country(self):
        return json.dumps({'count': self._get_count('"group"', 'group', True)})

    def organization(self):
        return json.dumps({'count': self._get_count('"group"', 'organization', True)})

    def source(self):
        return json.dumps({'count': 20})

    def tag(self):
        return json.dumps({'count': self._get_count('tag', 'tag', False)})

    def format(self):
        q = sqlalchemy.text('''select count(distinct(format)) from resource where not format is null;''')
        result = model.Session.connection().execute(q, entity_id=id).scalar()
        return json.dumps({'count': result})

    def license(self):
        q = sqlalchemy.text('''select count(distinct(license_id)) from package where not license_id is null;''')
        result = model.Session.connection().execute(q, entity_id=id).scalar()
        return json.dumps({'count': result})

    list = {
        'groups':country,
        'tags':tag,
        'organization':organization,
        'res_format':format,
        'license_id':license
    }


