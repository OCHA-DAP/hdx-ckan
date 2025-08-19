import pytest
import mock
import ckan.model as model

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.types import Context

from ckanext.hdx_theme.tests.conftest import DATASET_NAME, ORG_NAME, LOCATION_NAME
from ckanext.hdx_users.general_token_model import ObjectType
from ckanext.hdx_users.notifications_subscription_model import EventType

SYSADMIN_USER = 'test_sysadmin_user'
NORMAL_USER = 'test_normal_user'


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.hdx_supports_notifications')
def test_create_and_list_subscriptions(mock_supports_notifications, mock_novu_dao) -> None:
    factories.User(name=SYSADMIN_USER, sysadmin=True)
    user_dict = factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {'session': model.Session, 'user': NORMAL_USER}



    data_dict1 = {
        'user_id': NORMAL_USER,
        'object': DATASET_NAME,
        'object_type': ObjectType.DATASET.value,
        'event_type': EventType.DATASET_UPDATED.value,
    }

    subscription1 = tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)

    data_dict2 = {
        'user_id': NORMAL_USER,
        'object': ORG_NAME,
        'object_type': ObjectType.ORGANIZATION.value,
        'event_type': EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict2)

    data_dict3 = {
        'user_id': NORMAL_USER,
        'object': LOCATION_NAME,
        'object_type': ObjectType.GROUP.value,
        'event_type': EventType.NEW_DATASET_ADDED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict3)

    # List all subscriptions for the user (by username)
    data_dict_list = {
        'user_id': NORMAL_USER,
    }
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    dataset_id = tk.get_action('package_show')({'session': model.Session}, {'id': DATASET_NAME})['id']
    org_id = tk.get_action('organization_show')({'session': model.Session}, {'id': ORG_NAME})['id']
    location_id = tk.get_action('group_show')({'session': model.Session}, {'id': LOCATION_NAME})['id']
    assert len(subscriptions) == 3
    assert subscriptions[2]['object'] == dataset_id
    assert subscriptions[1]['object'] == org_id
    assert subscriptions[0]['object'] == location_id

    # List all subscriptions by user id
    data_dict_list = {
        'user_id': user_dict['id'],
    }
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    assert len(subscriptions) == 3

    # delete first subscription
    delete_subscription_id = subscriptions[0]['id']
    tk.get_action('hdx_notifications_subscription_delete')(context, {'token': subscription1['unsubscribe_token']})
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, data_dict_list)
    assert len(subscriptions) == 2


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.hdx_supports_notifications')
def test_subscription_not_accesible_by_different_user(mock_supports_notifications, mock_novu_dao) -> None:
    # Create a subscription for NORMAL_USER
    factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {'session': model.Session, 'user': NORMAL_USER}

    data_dict1 = {
        'user_id': NORMAL_USER,
        'object': DATASET_NAME,
        'object_type': ObjectType.DATASET.value,
        'event_type': EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)

    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, {})
    assert len(subscriptions) == 1

    # Try to access the subscription with a different user
    another_user = factories.User(name='another_user', sysadmin=False)
    context = {'session': model.Session, 'user': another_user['name']}
    subscriptions = tk.get_action('hdx_notifications_subscription_list')(context, {})
    assert len(subscriptions) == 0



# Test that a subscription cannot be created by a different user
@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
@mock.patch('ckanext.hdx_users.helpers.novu_interaction.hdx_supports_notifications')
def test_different_user_cannot_create_subscription(mock_supports_notifications, mock_novu_dao):
    # Create a subscription for NORMAL_USER
    factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {'session': model.Session, 'user': NORMAL_USER}

    data_dict1 = {
        'user_id': NORMAL_USER,
        'object': DATASET_NAME,
        'object_type': ObjectType.DATASET.value,
        'event_type': EventType.DATASET_UPDATED.value,
    }

    tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)

    # Try to create a subscription for NORMAL_USER by another user
    another_user = factories.User(name='another_user', sysadmin=False)
    data_dict1['user_id'] = another_user['name']

    with pytest.raises(tk.NotAuthorized):
        tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)


# Test that a subscription cannot be created by an anonymous user
@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'dataset_with_uploaded_resource')
def test_anonymous_user_cannot_create_subscription():
    factories.User(name=NORMAL_USER, sysadmin=False)
    context: Context = {'session': model.Session}

    data_dict1 = {
        'user_id': NORMAL_USER,
        'object': DATASET_NAME,
        'object_type': ObjectType.DATASET.value,
        'event_type': EventType.DATASET_UPDATED.value,
    }

    with pytest.raises(tk.NotAuthorized):
        tk.get_action('hdx_notifications_subscription_create')(context, data_dict1)
