from flask import Blueprint, make_response

import ckan.plugins.toolkit as tk

_ = tk._
render = tk.render

hdx_dataset_old_links = Blueprint(u'hdx_dataset_old_links', __name__)


def _show_notification_page(message, id=None):
    template_data = {
        'data': {
            'notice': message,
            'dataset_id': "'{}'".format(id) if id else ""
        }
    }
    # response.status_int = 300
    html = render('contribute_flow/dataset_old_links.html', extra_vars=template_data)
    response = make_response(html)
    response.status_code = 300
    return response


def new_notification_page(id=None):
    message = _('In order to create a new dataset please use the "ADD DATA" button at the top of the page or click ')
    return _show_notification_page(message, id)


def edit_notification_page(id=None):
    message = _('In order to edit this dataset please use the "EDIT" button on the dataset view page or click ')
    return _show_notification_page(message, id)


def resource_new_notification_page(id=None):
    message = _('In order to create a new resource please use the "EDIT" button on the dataset view page or click ')
    return _show_notification_page(message, id)


def resource_edit_notification_page(id=None, resource_id=None):
    message = _('In order to edit this resource please use the "EDIT" button on the dataset view page or click ')
    return _show_notification_page(message, id)


def resources_notification_page(id=None):
    return _show_notification_page(None, id)


hdx_dataset_old_links.add_url_rule(u'/dataset/new', view_func=new_notification_page, methods=[u'GET', u'POST'])
hdx_dataset_old_links.add_url_rule(u'/dataset/edit/<id>', view_func=edit_notification_page, methods=[u'GET', u'POST'])
hdx_dataset_old_links.add_url_rule(u'/dataset/<id>/resource_edit/<resource_id>',
                                   view_func=resource_edit_notification_page, methods=[u'GET', u'POST'])
hdx_dataset_old_links.add_url_rule(u'/dataset/new_resource/<id>',
                                   view_func=resource_new_notification_page, methods=[u'GET', u'POST'])
hdx_dataset_old_links.add_url_rule(u'/dataset/resources/<id>',
                                   view_func=resources_notification_page, methods=[u'GET', u'POST'])
