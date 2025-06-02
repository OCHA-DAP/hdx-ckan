import logging

from flask import Blueprint

from ckan.common import current_user
from ckan.types import Context

import ckan.lib.base as base
import ckan.plugins.toolkit as tk
import ckan.model as model
from ckanext.hdx_users.controller_logic.dashboard_dataset_logic import DashboardDatasetLogic
from ckanext.hdx_users.general_token_model import ObjectType, get_by_type_and_user_id_and_object, TokenType
from ckanext.hdx_users.views.notification_platform import _generate_url_for

log = logging.getLogger(__name__)

render = tk.render
get_action = tk.get_action
request = tk.request
g = tk.g
h = tk.h
_ = tk._
abort = base.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized

hdx_user_dashboard = Blueprint(u'hdx_user_dashboard', __name__, url_prefix=u'/dashboard')


def datasets():
    """
    Dashboard tab for datasets. Modified to add the ability to change
    the order and ultimately filter datasets displayed
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'home.index')

    dashboard_dataset_logic = DashboardDatasetLogic(g.userobj).read()
    if dashboard_dataset_logic.redirect_result:
        return dashboard_dataset_logic.redirect_result
    else:
        return render('user/dashboard_datasets.html', extra_vars={
            'user_dict': dashboard_dataset_logic.user_dict,
            'search_data': dashboard_dataset_logic.search_data
        })


def notifications():
    """
    Notifications tab
    """

    if not current_user.is_authenticated:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'home.index')

    context: Context = {'model': model, 'session': model.Session, 'user': current_user.name}
    data_dict = {
        'user_id': current_user.id,
    }
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict)
    for subscription in subscriptions:
        object_type = ObjectType(subscription.get('object_type'))
        object_id = subscription.get('object')
        try:
            object_dict = _get_object_dict(object_type, object_id)
            unsubscribe_token = get_by_type_and_user_id_and_object(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, current_user.email, object_type, object_id)
            subscription['object_dict'] = object_dict
            subscription['object_link'] = _generate_url_for(object_type, object_id, True)
            subscription['unsubscribe_token'] = unsubscribe_token.token if unsubscribe_token else None
        except tk.ObjectNotFound:
            raise tk.ValidationError(f'{object_type.value} {object_id} does not exist')
        except Exception as e:
            log.error(f'Error retrieving target or user: {e}')
            raise e

    return render('user/dashboard_notifications.html', extra_vars={
        'subscriptions': subscriptions,
        'user_dict': current_user,
    })

def _get_object_dict(object_type, object_id):
    context: Context = {}

    action = None
    if object_type == ObjectType.DATASET.value:
        action = 'package_show'
    elif object_type == ObjectType.GROUP.value:
        action = 'group_show'
    elif object_type == ObjectType.ORGANIZATION.value:
        action = 'organization_show'
    elif object_type == ObjectType.CRISIS.value:
        action = 'page_show'

    if action:
        return tk.get_action(action)(context, {'id': object_id})
    else:
        return {}


hdx_user_dashboard.add_url_rule(u'/datasets', view_func=datasets)
hdx_user_dashboard.add_url_rule(u'/notifications', view_func=notifications)
