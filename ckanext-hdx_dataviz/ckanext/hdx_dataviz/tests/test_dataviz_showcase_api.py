import pytest
import six

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckanext.hdx_dataviz.tests import generate_test_showcase, USER, SYSADMIN, ORG, LOCATION


_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError

@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index', 'setup_user_data')
class TestDatavizShowcaseApi(object):

    def test_create_dataviz_showcase(self):
        showcase_dict = generate_test_showcase(USER, 'normal_showcase', True)
        assert showcase_dict['in_dataviz_gallery'] is False

    def test_update_dataviz_showcase(self):
        showcase_dict = generate_test_showcase(SYSADMIN, 'dataviz_showcase', True)
        showcase_dict['notes'] = 'Modified'

        try:
            context = {'model': model, 'session': model.Session, 'user': USER}
            _get_action('ckanext_showcase_update')(context, showcase_dict)
            assert False
        except NotAuthorized as e:
            assert True, 'An editor user should NOT be allowed to update a dataviz showcase'

    def test_update_normal_showcase(self):
        showcase_dict = generate_test_showcase(SYSADMIN, 'normal_showcase', False)
        showcase_dict['notes'] = 'Modified'
        assert 'dataviz_label' not in showcase_dict
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
        modified_dict = _get_action('ckanext_showcase_update')(context, showcase_dict)
        assert modified_dict['notes'] == 'Modified', 'A sysadmin should be able to update a normal showcase'

    def test_update_normal_showcase_with_in_dataviz_gallery_not_set(self):
        showcase_dict = generate_test_showcase(SYSADMIN, 'normal_showcase_in_dataviz_gallery_not_set', False)
        showcase_dict['notes'] = 'Modified'
        assert 'dataviz_label' not in showcase_dict
        del showcase_dict['in_dataviz_gallery']
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN}
        modified_dict = _get_action('ckanext_showcase_update')(context, showcase_dict)
        assert modified_dict['notes'] == 'Modified', 'A sysadmin should be able to update a normal showcase even ' \
                                                     'without having the "in_dataviz_gallery" parameter'

    def test_delete_normal_showcase(self):
        showcase_dict = generate_test_showcase(USER, 'normal_showcase', False)

        context = {'model': model, 'session': model.Session, 'user': USER}
        _get_action('ckanext_showcase_delete')(context, {'id': showcase_dict['id']})
        assert True, 'An editor user should be allowed to delete a normal showcase'

    def test_delete_dataviz_gallery_item(self):
        showcase_dict = generate_test_showcase(SYSADMIN, 'dataviz_showcase', True)

        try:
            context = {'model': model, 'session': model.Session, 'user': USER}
            _get_action('ckanext_showcase_delete')(context, {'id': showcase_dict['id']})
            assert False
        except NotAuthorized as e:
            assert True, 'An editor user should NOT be allowed to delete a dataviz showcase'

    @pytest.mark.skipif(six.PY3, reason=u"The user_extras plugin is not available on PY3 yet")
    def test_update_dataviz_with_carousel_permission(self):
        from ckanext.hdx_users.helpers.permissions import Permissions

        showcase_dict = generate_test_showcase(SYSADMIN, 'dataviz_showcase', True)
        showcase_dict['notes'] = 'Modified'
        showcase_dict['image_url'] = None
        user_with_permission = factories.User(name='user_with_permission', email='another_user@hdx.hdxtest.org')
        Permissions(user_with_permission['id']).set_permissions(
            {'user': SYSADMIN},
            [Permissions.PERMISSION_MANAGE_CAROUSEL]
        )

        context = {'model': model, 'session': model.Session, 'user': 'user_with_permission'}
        showcase_dict = _get_action('ckanext_showcase_update')(context, showcase_dict)
        assert showcase_dict['in_dataviz_gallery'] is True, \
            'A user with carousel permission should be allowed to update a dataviz showcase'

        del showcase_dict['dataviz_label']
        try:
            _get_action('ckanext_showcase_update')(context, showcase_dict)
            assert False
        except ValidationError as e:
            assert True, 'Validation should fail for dataviz showcases without "dataviz_label"'
