import pytest
import mock

import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST
from ckanext.hdx_users.general_token_model import (
    get_by_token,
    get_by_type_and_user_id,
    generate_new_token_obj,
    TokenType,
    ObjectType,
    State
)
from ckanext.hdx_users.notifications_subscription_model import EventType, list_notifications_subscriptions, \
    generate_notifications_subscription, get

_get_action = tk.get_action
g = tk.g
config = tk.config

SYSADMIN_USER = 'some_sysadmin_user'
DATASET_NAME = 'dataset_name_for_notification_platform'
DATASET_ID = None
LOCATION_NAME = 'some_location_for_notification_platform'
ORG_NAME = 'org_name_for_notification_platform'
DATASET_DICT = {
    'package_creator': 'test function',
    'private': False,
    'dataset_date': '[1960-01-01 TO 2012-12-31]',
    'caveats': 'These are the caveats',
    'license_other': 'TEST OTHER LICENSE',
    'methodology': 'This is a test methodology',
    'dataset_source': 'Test data',
    'license_id': 'hdx-other',
    # "name": DATASET_NAME,
    'notes': 'This is a test dataset',
    # "title": "Test Dataset " + DATASET_NAME,
    # "owner_org": ORG_NAME,
    'groups': [{'name': LOCATION_NAME}],
    'data_update_frequency': '30',
    'maintainer': SYSADMIN_USER
}

RESOURCE_LIST = [
    {
        'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test1.csv',
        'resource_type': 'file.upload',
        'format': 'CSV',
        'name': 'hdx_test1.csv',
    }
]


def _create_dataset(with_resources=True):
    global DATASET_ID
    context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    dataset_dict = dict(DATASET_DICT)
    dataset_dict['name'] = DATASET_NAME
    dataset_dict['title'] = 'Test Dataset ' + dataset_dict['name'],
    dataset_dict['owner_org'] = ORG_NAME

    if with_resources:
        dataset_dict['resources'] = RESOURCE_LIST

    package_dict = _get_action('package_create')(context, dataset_dict)
    DATASET_ID = package_dict['id']
    return package_dict


def _create_org():
    org_name = ORG_NAME
    factories.Organization(
        name=org_name,
        title='ORG NAME ' + org_name,
        users=[
            {'name': SYSADMIN_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )
    return org_name


@pytest.fixture()
def setup_data():
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    g.userobj = model.User.by_name(SYSADMIN_USER)
    group = factories.Group(name=LOCATION_NAME)
    _create_org()

    _create_dataset()

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'with_request_context', 'setup_data')
class TestNotificationPlatform(object):

    @mock.patch(
        'ckanext.hdx_users.views.notification_platform.hdx_mailer')
    @mock.patch(
        'ckanext.hdx_users.controller_logic.notification_platform_logic.hdx_supports_notifications')
    def test_user_subscribing_to_dataset(self, check_supports_notification, hdx_mailer_mock, app):
        requester_email_address = 'test@test.test'
        check_supports_notification.return_value = True
        subscribe_url = tk.url_for('hdx_notifications.subscription_confirmation')
        #User subscribes to the dataset
        response = app.post(
            subscribe_url,
            data={
                'email': requester_email_address,
                'object_id': DATASET_NAME,
                'object_type': ObjectType.DATASET.value,
            },
        )
        assert response.json.get('success')

        # Check that the validation token was created and is active
        tokens = get_by_type_and_user_id(
            TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION,
            'test@test.test'
        )
        assert len(tokens) == 1
        assert tokens[0].state == State.ACTIVE

    # @mock.patch('ckanext.hdx_users.views.notification_platform._add_notification_subscription')
    # def test_user_validates_email(self, add_notification_subscription_mock, app):
    #     requester_email_address = 'test_validation@test.test'
    #     token_obj = generate_new_token_obj(
    #         model.Session, TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION,
    #         requester_email_address, object_type=ObjectType.DATASET, object_id=DATASET_ID
    #     )
    #     assert token_obj.state == State.ACTIVE
    #
    #     validate_url = tk.url_for('hdx_notifications.subscribe_to_dataset', token=token_obj.token)
    #     response = app.get(
    #         validate_url,
    #         headers={
    #             'User-Agent': 'TEST USER AGENT'
    #         },
    #     )
    #
    #     modified_token = get_by_token(token_obj.token)
    #     assert modified_token.state == State.INACTIVE
    #
    #     unsubscribe_tokens = get_by_type_and_user_id(TokenType.UNSUBSCRIBE_FOR_NOTIFICATION, requester_email_address)
    #     assert len(unsubscribe_tokens) == 1
    #     assert unsubscribe_tokens[0].state == State.ACTIVE

    @mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
    def test_user_unsubscribing_from_dataset(self, mock_novu_dao, app):
        user_dict = factories.User(name='standard_user')

        unsubscribe_token_obj = generate_new_token_obj(
            model.Session, TokenType.UNSUBSCRIBE_FOR_NOTIFICATION,
            user_dict['id'], object_type=ObjectType.DATASET, object_id=DATASET_ID
        )
        assert unsubscribe_token_obj.state == State.ACTIVE


        subscription = generate_notifications_subscription(
            session=model.Session,
            user_id=user_dict['id'],
            object_type=ObjectType.DATASET,
            object=DATASET_ID,
            event_type=EventType.NEW_DATASET_ADDED,
            unsubscribe_token_id=unsubscribe_token_obj.id,
        )

        unsubscribe_url = tk.url_for('hdx_notifications.unsubscribe_confirmation')
        response = app.post(
            unsubscribe_url,
            data={
                'token': unsubscribe_token_obj.token
            },
        )

        modified_token = get_by_token(unsubscribe_token_obj.token)
        assert modified_token.state == State.INACTIVE

        modified_subscription = get(model.Session, subscription.id)
        assert modified_subscription.state == State.DELETED

    @mock.patch('flask_login.utils._get_user')
    @mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
    @mock.patch('ckanext.hdx_users.helpers.novu_interaction.hdx_supports_notifications')
    def test_authenticated_user_subscription_to_object(
        self, mock_supports_notifications, mock_novu_dao, current_user, app
    ):
        user_dict = factories.User(name='standard_user')
        user = model.User.get(user_dict['id'])
        org = model.Group.get(ORG_NAME)
        current_user.return_value = user
        # token = factories.APIToken(user='standard_user', expires_in=2, unit=60 * 60)
        # headers = {'Authorization': token['token']}
        subscribe_url = tk.url_for('hdx_notifications.subscription_confirmation')
        response = app.post(
            subscribe_url,
            data={
                'object_type': ObjectType.ORGANIZATION.value,
                'object_id': ORG_NAME,
                'dataset_updates': 'true',
            },
            # headers=headers
        )
        assert response.status_code == 200

        user_subscriptions = list_notifications_subscriptions(session=model.Session, user_id=user_dict['id'])
        assert len(user_subscriptions) == 1
        subscription = user_subscriptions[0]

        assert subscription['object_type'] == ObjectType.ORGANIZATION.value
        assert subscription['object'] == org.id
        # assert subscription['event_type'] == EventType.DATASET_UPDATED.value
        assert subscription['event_type'] == EventType.NEW_DATASET_ADDED.value

    # @mock.patch('ckanext.hdx_users.views.notification_platform._add_notification_subscription')
    @mock.patch(
        'ckanext.hdx_users.views.notification_platform.hdx_mailer')
    @mock.patch('ckanext.hdx_users.helpers.novu_interaction.NovuDAO')
    @mock.patch('ckanext.hdx_users.helpers.novu_interaction.hdx_supports_notifications')
    @mock.patch(
        'ckanext.hdx_users.controller_logic.notification_platform_logic.hdx_supports_notifications')
    def test_anon_user_subscribe_to_object(
        self, check_supports_notification, mock_supports_notifications, mock_novu_dao, hdx_mailer_mock, app
    ):

        # Create email validation request (and email validation token)
        requester_email_address = 'test@test.test'
        check_supports_notification.return_value = True
        subscribe_url = tk.url_for('hdx_notifications.subscription_confirmation')
        # User subscribes to the dataset
        response = app.post(
            subscribe_url,
            data={
                'email': requester_email_address,
                'object_id': DATASET_NAME,
                'object_type': ObjectType.DATASET.value,
                'dataset_updates': 'true',
            },
        )
        assert response.json.get('success')

        # Subscribe to object using the email validation token
        tokens = get_by_type_and_user_id(
            TokenType.EMAIL_VALIDATION_FOR_NOTIFICATION,
            'test@test.test'
        )
        assert len(tokens) == 1
        subscribe_to_object_url = tk.url_for(
            'hdx_notifications.subscribe_to_object',
            token=tokens[0].token
        )
        response = app.get(
            subscribe_to_object_url,
            data={'token': tokens[0].token},
            headers={'User-Agent': 'TEST USER AGENT'},
        )

        assert response.status_code == 200

        user_subscriptions = list_notifications_subscriptions(session=model.Session)
        assert len(user_subscriptions) == 1
        subscription = user_subscriptions[0]

        assert subscription['object_type'] == ObjectType.DATASET.value
        assert subscription['object'] == DATASET_ID
        # assert subscription['event_type'] == EventType.DATASET_UPDATED.value
        assert subscription['event_type'] == EventType.NEW_DATASET_ADDED.value

