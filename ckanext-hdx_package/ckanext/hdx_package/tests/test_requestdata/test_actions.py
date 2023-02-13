import logging as logging

import ckan.model as model
import ckan.tests.legacy as tests
import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.tests.hdx_test_with_requestdata_type_and_orgs as hdx_test_with_requestdata_type_and_orgs

import json

log = logging.getLogger(__name__)

ValidationError = tk.ValidationError
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound


class TestRequestdataActions(hdx_test_with_requestdata_type_and_orgs.HDXWithRequestdataTypeAndOrgsTest):

    @classmethod
    def setup_class(cls):
        cls.USERS_USED_IN_TEST.append('johndoe1')
        cls.testsysadmin = model.User.by_name('testsysadmin')
        cls.johndoe1 = model.User.by_name('johndoe1')
        super(TestRequestdataActions, cls).setup_class()

    @classmethod
    def _create_test_data(cls):
        super(TestRequestdataActions, cls)._create_test_data(create_datasets=True, create_members=True)

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_create_requestdata_valid(self):

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_1"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)
        assert 'requestdata_id' in result

    def test_create_requestdata_valid_other_values(self):

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_2"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'other',
            'sender_organization_id_other': 'hdx-test-org',
            'sender_organization_type': 'other',
            'sender_organization_type_other': 'Research',
            'sender_intend': 'other',
            'sender_intend_other': 'Testing Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)
        assert 'requestdata_id' in result

    def test_create_requestdata_missing_values_raises_error(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            result = self._get_action('requestdata_request_create')(context, {})
            assert False
        except ValidationError as ex:
            assert ex.error_dict['message_content'] == [u'Missing value']
            assert ex.error_dict['sender_name'] == [u'Missing value']
            assert ex.error_dict['email_address'] == [u'Missing value']
            assert ex.error_dict['package_id'] == [u'Missing value']
            assert ex.error_dict['sender_country'] == [u'Missing value']
            assert ex.error_dict['sender_organization_id'] == [u'Missing value']
            assert ex.error_dict['sender_organization_type'] == [u'Missing value']
            assert ex.error_dict['sender_intend'] == [u'Missing value']
            assert len(ex.error_dict) == 8
        assert True

    def test_create_requestdata_missing_other_values_raises_error(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_12"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'other',
            'sender_organization_id_other': '',
            'sender_organization_type': 'other',
            'sender_organization_type_other': '',
            'sender_intend': 'other',
            'sender_intend_other': ''
        }

        try:
            result = self._get_action('requestdata_request_create')(context, data_dict)
            assert False
        except ValidationError as ex:
            assert ex.error_dict['sender_organization_id_other'] == [u'Missing value']
            assert ex.error_dict['sender_organization_type_other'] == [u'Missing value']
            assert ex.error_dict['sender_intend_other'] == [u'Missing value']
            assert len(ex.error_dict) == 3
        assert True

    def test_create_requestdata_raises_auth_error(self):
        context = {'ignore_auth': False}
        try:
            result = self._get_action('requestdata_request_create')(context, {})
            assert False
        except NotAuthorized as ex:
            assert True
        assert True

    def test_create_requestdata_invalid_email(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_1"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'non@existing@ro.ro',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }
        try:
            result = self._get_action('requestdata_request_create')(context, data_dict)
            assert False
        except ValidationError as ex:
            assert ex.error_dict.get('email_address') == [u'Please provide a valid email address.']
        except Exception as ex:
            assert True
        assert True

    def test_create_requestdata_pending_request(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_3"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)

        try:
            result = self._get_action('requestdata_request_create')(context, data_dict)
            assert False
        except ValidationError as ex:
            assert ex.error_dict.get('package_id') == [
                u'You already have a pending request. Please wait for the reply.']
        assert True

    def test_create_requestdata_invalid_package(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_1"})
        data_dict = {
            'package_id': 'non_existing_package_id',
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }
        try:
            result = self._get_action('requestdata_request_create')(context, data_dict)
            assert False
        except ValidationError as ex:
            assert ex.error_dict['package_id'] == [u'Not found: Dataset']
        except Exception as ex:
            assert True
        assert True

    def test_show_requestdata_valid(self):
        testsysadmin_obj = model.User.by_name('testsysadmin')
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_4"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)
        assert 'requestdata_id' in result

        requestdata_id = result.get('requestdata_id')

        data_dict_show = {
            'id': requestdata_id,
            'package_id': data_dict['package_id']
        }

        result = self._get_action('requestdata_request_show')(context, data_dict_show)

        assert result['package_id'] == data_dict['package_id']
        assert result['sender_name'] == data_dict['sender_name']
        assert result['message_content'] == data_dict['message_content']
        assert result['email_address'] == data_dict['email_address']
        assert result['data_shared'] is False
        assert result['state'] == 'new'
        assert result['sender_user_id'] == testsysadmin_obj.id

        context = {'ignore_auth': False}
        try:
            result = self._get_action('requestdata_request_show')(context, data_dict_show)
            assert False
        except NotAuthorized as ex:
            assert True

    def test_show_requestdata_valid_extras(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_5"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)

        assert 'requestdata_id' in result

        requestdata_id = result.get('requestdata_id')

        data_dict_show = {
            'id': requestdata_id,
            'package_id': data_dict['package_id']
        }

        result = self._get_action('requestdata_request_show')(context, data_dict_show)

        assert 'extras' in result

        extras = json.loads(result['extras'])

        assert 'country' in extras
        assert 'organization_id' in extras
        assert 'organization_name' in extras
        assert 'organization_member' in extras
        assert 'organization_type' in extras
        assert 'intend' in extras

    def test_show_requestdata_valid_warning_sign_user_not_part_of_organization(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'johndoe1'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_6"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'other',
            'sender_organization_id_other': 'non existing organization',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)

        assert 'requestdata_id' in result

        requestdata_id = result.get('requestdata_id')

        data_dict_show = {
            'id': requestdata_id,
            'package_id': data_dict['package_id']
        }

        result = self._get_action('requestdata_request_show')(context, data_dict_show)

        assert 'extras' in result

        extras = json.loads(result['extras'])

        assert 'organization_member' in extras and extras.get('organization_member') is False

    def test_show_requestdata_valid_no_warning_sign_user_is_part_of_organization(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'johndoe1'}
        pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_7"})
        data_dict = {
            'package_id': pkg.get('id'),
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': 'test@test.com',
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        result = self._get_action('requestdata_request_create')(context, data_dict)

        assert 'requestdata_id' in result

        requestdata_id = result.get('requestdata_id')

        data_dict_show = {
            'id': requestdata_id,
            'package_id': data_dict['package_id']
        }

        result = self._get_action('requestdata_request_show')(context, data_dict_show)

        assert 'extras' in result

        extras = json.loads(result['extras'])

        assert 'organization_member' in extras and extras.get('organization_member') is True

    def test_show_requestdata_missing_values(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            result = self._get_action('requestdata_request_show')(context, {})
            assert False
        except ValidationError as ex:
            assert ex.error_dict['id'] == [u'Missing value']
            assert ex.error_dict['package_id'] == [u'Missing value']
            assert True
        assert True

    def test_show_requestdata_invalid_package(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            result = self._get_action('requestdata_request_show')(context, {'package_id': 'non_existing_package_id'})
            assert False
        except ValidationError as ex:
            assert ex.error_dict['package_id'] == [u'Not found: Dataset']
            assert True
        assert True

    def test_show_requestdata_request_not_found(self):
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        try:
            pkg = self._get_action('package_show')(context, {"id": "test_activity_request_data_1"})
            data_dict = {
                'package_id': 'non_existing_package_id',
                'id': pkg.get('id'),
            }
            result = self._get_action('requestdata_request_show')(context, data_dict)
            assert False
        except ValidationError as ex:
            assert 'package_id' in ex.error_dict
            assert True
        assert True

    def test_requestdata_request_list_for_current_user(self):
        testsysadmin_obj = model.User.by_name('testsysadmin')
        johndoe1 = model.User.by_name('johndoe1')
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        data_dict = {
            'sender_name': 'John Doe',
            'message_content': 'I want to add additional data.',
            'organization': 'hdx-test-org',
            'email_address': johndoe1.email,
            'sender_country': 'Romania',
            'sender_organization_id': 'hdx-test-org',
            'sender_organization_type': 'Military',
            'sender_intend': 'Research Purposes'
        }

        for package_id in ['test_activity_request_data_8', 'test_activity_request_data_9']:
            pkg = self._get_action('package_show')(context, {"id": package_id})
            data_dict['package_id'] = pkg.get('id')
            result = self._get_action('requestdata_request_create')(context, data_dict)

        context = {'auth_user_obj': testsysadmin_obj}

        try:
            result = self._get_action('requestdata_request_list_for_current_user')(context, {})
            assert True
        except Exception as ex:
            assert False

        assert len(result) >= 2


class TestRequestdataForOrgActions(hdx_test_with_requestdata_type_and_orgs.HDXWithRequestdataTypeAndOrgsTest):

    @classmethod
    def setup_class(cls):
        cls.USERS_USED_IN_TEST.append('johndoe1')
        cls.testsysadmin = model.User.by_name('testsysadmin')
        cls.johndoe1 = model.User.by_name('johndoe1')
        super(TestRequestdataForOrgActions, cls).setup_class()

    @classmethod
    def _create_test_data(cls):
        super(TestRequestdataForOrgActions, cls)._create_test_data(create_datasets=True, create_members=True)

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_requestdata_request_list_for_organization(self):

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'johndoe1'}
        for package_id in ['test_activity_request_data_10', 'test_activity_request_data_11']:
            pkg = self._get_action('package_show')(context, {"id": package_id})
            data_dict = {
                'package_id': pkg.get('id'),
                'sender_name': 'John Doe',
                'message_content': 'I want to add additional data.',
                'organization': 'hdx-test-org',
                'email_address': 'test@test.com',
                'sender_country': 'Romania',
                'sender_organization_id': 'hdx-test-org',
                'sender_organization_type': 'Military',
                'sender_intend': 'Research Purposes'
            }
            try:
                result = self._get_action('requestdata_request_create')(context, data_dict)
            except Exception as ex:
                assert False
        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        result = self._get_action('requestdata_request_list_for_organization')(context, {"org_id": "hdx-test-org"})
        assert len(result) == 2

    def test_requestdata_request_list_for_organization_missing_org_id(self):

        context = {'ignore_auth': True, 'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        try:
            result = self._get_action('requestdata_request_list_for_organization')(context, {})
            assert False
        except ValidationError as ex:
            assert ex.error_dict['org_id'] == [u'Missing value']

    def test_requestdata_notification_create_valid(self):
        johndoe1 = model.User.by_name('johndoe1')
        context = {'user': johndoe1.name}
        data_dict = {
            'users': [{'id': johndoe1.id}]
        }
        result = self._get_action('requestdata_notification_create')(context, data_dict)
        assert result[0].seen is False

        result = self._get_action('requestdata_notification_for_current_user')(context, {})
        assert result is False

        data_dict = {
            'user_id': johndoe1.id
        }
        result = self._get_action('requestdata_notification_change')(context, data_dict)
        assert result.seen is True
