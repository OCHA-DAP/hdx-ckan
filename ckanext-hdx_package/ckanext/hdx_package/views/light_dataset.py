from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.common import g

get_action = tk.get_action
render = tk.render

hdx_light_dataset = Blueprint(u'hdx_light_dataset', __name__, url_prefix=u'/m/dataset')


def read(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True
    }
    data_dict = {
        u'id': id
    }
    dataset_dict = get_action('package_show')(context, data_dict)

    return render(u'light/dataset/read.html', {'dataset_dict': dataset_dict})


hdx_light_dataset.add_url_rule(u'/<id>', view_func=read)
