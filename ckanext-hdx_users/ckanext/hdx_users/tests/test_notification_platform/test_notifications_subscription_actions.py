import pytest
import ckan.model as model

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.types import Context

from ckanext.hdx_theme.tests.conftest import DATASET_NAME, ORG_NAME, LOCATION_NAME
from ckanext.hdx_users.notifications_subscription_model import TargetType, EventType

SYSADMIN_USER = 'test_sysadmin_user'
NORMAL_USER = 'test_normal_user'


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
def test_create_and_list_subscriptions() -> None:
    factories.User(name=SYSADMIN_USER, sysadmin=True)
    user_dict = factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {"session": model.Session, "user": NORMAL_USER}



    data_dict1 = {
        "user_id": NORMAL_USER,
        "target": DATASET_NAME,
        "target_type": TargetType.DATASET.value,
        "event_type": EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)

    data_dict2 = {
        "user_id": NORMAL_USER,
        "target": ORG_NAME,
        "target_type": TargetType.ORGANIZATION.value,
        "event_type": EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict2)

    data_dict3 = {
        "user_id": NORMAL_USER,
        "target": LOCATION_NAME,
        "target_type": TargetType.GROUP.value,
        "event_type": EventType.NEW_DATASET_ADDED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict3)

    # List all subscriptions for the user (by username)
    data_dict_list = {
        "user_id": NORMAL_USER,
    }
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    assert len(subscriptions) == 3
    assert subscriptions[0]['target'] == DATASET_NAME
    assert subscriptions[1]['target'] == ORG_NAME
    assert subscriptions[2]['target'] == LOCATION_NAME

    # List all subscriptions by user id
    data_dict_list = {
        "user_id": user_dict['id'],
    }
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    assert len(subscriptions) == 3

    # delete first subscription
    delete_subscription_id = subscriptions[0]['id']
    tk.get_action('hdx_notifications_subscription_delete')(context, {'id': delete_subscription_id})
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    assert len(subscriptions) == 2


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
def test_subscription_not_accesible_by_different_user():
    # Create a subscription for NORMAL_USER
    factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {"session": model.Session, "user": NORMAL_USER}

    data_dict1 = {
        "user_id": NORMAL_USER,
        "target": DATASET_NAME,
        "target_type": TargetType.DATASET.value,
        "event_type": EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)

    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, {})
    assert len(subscriptions) == 1

    # Try to access the subscription with a different user
    another_user = factories.User(name='another_user', sysadmin=False)
    context = {"session": model.Session, "user": another_user['name']}
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, {})
    assert len(subscriptions) == 0





