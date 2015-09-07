'''
Created on Sep 02, 2015

@author: alexandru-m-g
'''

from pylons import config

import ckan.logic as logic
import ckan.model as model
import sqlalchemy


@logic.side_effect_free
def hdx_resource_id_list(context, data_dict):
    logic.check_access('hdx_resource_id_list', context, data_dict)

    q = sqlalchemy.text("SELECT id FROM resource where state='active' ORDER BY id;")
    result = model.Session.connection().execute(q, entity_id=id)
    ids = [row[0] for row in result]
    return ids
