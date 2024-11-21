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

_get_action = tk.get_action
g = tk.g
config = tk.config

SYSADMIN_USER = 'some_sysadmin_user'
DATASET_NAME = 'dataset_name_for_notification_platform'
DATASET_ID = None
LOCATION_NAME = 'some_location_for_notification_platform'
ORG_NAME = 'org_name_for_notification_platform'
DATASET_DICT = {
    "package_creator": "test function",
    "private": False,
    "dataset_date": "[1960-01-01 TO 2012-12-31]",
    "caveats": "These are the caveats",
    "license_other": "TEST OTHER LICENSE",
    "methodology": "This is a test methodology",
    "dataset_source": "Test data",
    "license_id": "hdx-other",
    # "name": DATASET_NAME,
    "notes": "This is a test dataset",
    # "title": "Test Dataset " + DATASET_NAME,
    # "owner_org": ORG_NAME,
    "groups": [{"name": LOCATION_NAME}],
    "data_update_frequency": "30",
    "maintainer": SYSADMIN_USER
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
    dataset_dict['title'] = "Test Dataset " + dataset_dict['name'],
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
def setup_data(migrate_db_for):
    migrate_db_for('hdx_users')
    factories.User(name=SYSADMIN_USER, email='some_user@hdx.hdxtest.org', sysadmin=True)
    g.userobj = model.User.by_name(SYSADMIN_USER)
    group = factories.Group(name=LOCATION_NAME)
    _create_org()

    _create_dataset()


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'with_request_context', 'setup_data')
class TestNotificationPlatform(object):

    @mock.patch(
        'ckanext.hdx_users.controller_logic.notification_platform_logic.check_notifications_enabled_for_dataset')
    def test_user_subscribing_to_dataset(self, check_dataset_enabled_mock, app):
        requester_email_address = 'test@test.test'
        check_dataset_enabled_mock.return_value = True
        subscribe_url = tk.url_for('hdx_notifications.subscription_confirmation')
        #User subscribes to the dataset
        response = app.post(
            subscribe_url,
            data={
                'email': requester_email_address,
                'dataset_id': DATASET_NAME,
            },
        )
        assert response.json.get('success')

        # Check that the validation token was created and is active
        tokens = get_by_type_and_user_id(
            TokenType.EMAIL_VALIDATION_FOR_DATASET,
            'test@test.test'
        )
        assert len(tokens) == 1
        assert tokens[0].state == State.ACTIVE

    @mock.patch('ckanext.hdx_users.views.notification_platform._add_notification_subscription')
    def test_user_validates_email(self, add_notification_subscription_mock, app):
        requester_email_address = 'test_validation@test.test'
        token_obj = generate_new_token_obj(
            model.Session, TokenType.EMAIL_VALIDATION_FOR_DATASET,
            requester_email_address, object_type=ObjectType.DATASET, object_id=DATASET_ID
        )
        assert token_obj.state == State.ACTIVE

        validate_url = tk.url_for('hdx_notifications.subscribe_to_dataset', token=token_obj.token)
        response = app.get(
            validate_url,
            headers={
                'User-Agent': 'TEST USER AGENT'
            },
        )

        modified_token = get_by_token(token_obj.token)
        assert modified_token.state == State.INACTIVE

        unsubscribe_tokens = get_by_type_and_user_id(TokenType.UNSUBSCRIBE_FOR_DATASET, requester_email_address)
        assert len(unsubscribe_tokens) == 1
        assert unsubscribe_tokens[0].state == State.ACTIVE

    @mock.patch('ckanext.hdx_users.views.notification_platform._delete_notification_subscription')
    def test_user_unsubscribing_from_dataset(self, delete_notification_subscription, app):
        requester_email_address = 'test_unsubscribing@test.test'
        token_obj = generate_new_token_obj(
            model.Session, TokenType.UNSUBSCRIBE_FOR_DATASET,
            requester_email_address, object_type=ObjectType.DATASET, object_id=DATASET_ID
        )
        assert token_obj.state == State.ACTIVE

        unsubscribe_url = tk.url_for('hdx_notifications.unsubscribe_confirmation', token=token_obj.token)
        response = app.post(
            unsubscribe_url,
            data={
                'token': token_obj.token
            },
        )

        modified_token = get_by_token(token_obj.token)
        assert modified_token.state == State.INACTIVE
