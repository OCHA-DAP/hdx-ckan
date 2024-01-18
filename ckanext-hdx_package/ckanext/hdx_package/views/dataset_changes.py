from flask import Blueprint

from ckanext.activity.views import package_changes_multiple


hdx_dataset_changes = Blueprint(u'hdx_dataset_changes', __name__, url_prefix=u'/dataset-changes')

hdx_dataset_changes.add_url_rule(u'/view', view_func=package_changes_multiple)
