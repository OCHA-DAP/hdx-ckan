from ckan import model as model

import ckan.plugins.toolkit as tk

_get_action = tk.get_action

USER = 'some_user'
SYSADMIN = 'some_sysadmin'
LOCATION = 'some_location'
ORG = 'some_org_name'

#
#
# def generate_test_showcase(username, showcase_name, in_dataviz_gallery):
#     dataset = {
#         'name': showcase_name,
#         'title': 'Test Showcase ' + showcase_name,
#         'notes': 'This is a test showcase',
#         'in_dataviz_gallery': in_dataviz_gallery,
#         'dataviz_label': 'Test Label',
#     }
#
#     context = {'model': model, 'session': model.Session, 'user': username}
#     showcase_dict = _get_action('ckanext_showcase_create')(context, dataset)
#     return showcase_dict
