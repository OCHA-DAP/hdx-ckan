from flask import Blueprint

from ckan.views.dataset import changes_multiple


hdx_dataset_changes = Blueprint(u'hdx_dataset_changes', __name__, url_prefix=u'/dataset-changes')

hdx_dataset_changes.add_url_rule(u'/view', view_func=changes_multiple)
