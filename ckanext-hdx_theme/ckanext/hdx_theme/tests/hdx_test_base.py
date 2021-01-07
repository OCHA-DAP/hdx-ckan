'''
Created on Jun 16, 2014

@author: alexandru-m-g
'''

import logging
import ckan.lib.create_test_data as ctd
import ckan.model as model
import ckan.lib.search as search
import ckan.logic as logic

import ckan.plugins.toolkit as tk
import ckan.tests.helpers as helpers

import ckanext.hdx_package.actions.create as hdx_actions
import ckanext.hdx_package.helpers.caching as caching


config = tk.config

log = logging.getLogger(__name__)

original_package_create = hdx_actions.package_create


# def _get_test_app():
#     config['ckan.legacy_templates'] = False
#     app = ckanconfig.middleware.make_app(config['global_conf'], **config)
#     app = webtest.TestApp(app)
#     return app

_get_test_app = helpers._get_test_app


def load_plugin(plugin):
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.update(plugin.strip().split())
    config['ckan.plugins'] = ' '.join(plugins)


class HdxBaseTest(object):
    '''
    NOTE: Since more fields have been made mandatory for a dataset the process of creating test
    data at the beginning of a test suit was failing.
    Therefore the package_create action is now wrapped while running the tests to automatically
    populate some missing fields.
    See replace_package_create ()
    '''

    app = None
    original_config = None
    USERS_USED_IN_TEST = ['tester', 'testsysadmin']

    @classmethod
    def _set_user_api_keys(cls):
        for username in cls.USERS_USED_IN_TEST:
            user = model.User.by_name(username)
            if user:
                user.email = username + '@test-domain.com'
                user.apikey = username + '_apikey'

        model.Session.commit()

    @classmethod
    def _create_test_data(cls):
        ctd.CreateTestData.create()

    @classmethod
    def _load_plugins(cls):
        load_plugin('ytp_request hdx_org_group hdx_theme')

    @classmethod
    def _change_config(self, config):
        '''
        Allows subclasses to change the config before the "app" and the test data are created.
        The subclass does not need to worry about cleanup of the config as this class
        restores the original config in teardown_class()
        '''
        pass

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()

        # so that we can search for strings in the HTTP response
        config['ckan.use_pylons_response_cleanup_middleware'] = False
        cls._change_config(config)

        search.clear_all()
        helpers.reset_db()
        caching.invalidate_group_caches()
        # cls._load_plugins()
        cls.app = _get_test_app()

        cls.replace_package_create()

        cls._create_test_data()

        cls._set_user_api_keys()

    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        # model.repo.rebuild_db()

        config.clear()
        config.update(cls.original_config)
        logic._actions['package_create'] = original_package_create

    @classmethod
    def replace_package_create(cls):
        '''
        override this with an empty function in your class if you want the original
        package_create function that does not automatically populate some of the mandatory
        fields. ( More info in the class description )
        '''

        # cls.use_package_create_wrapper flag can be also overwritten temporarily in your test class
        cls.use_package_create_wrapper = True

        def package_create_wrapper(context, data_dict):
            if cls.use_package_create_wrapper:
                if not data_dict.get('license_id'):
                    data_dict['license_id'] = 'cc'

                private = False if str(data_dict.get('private', '')).lower() == 'false' else True
                if not data_dict.get('maintainer'):
                    data_dict['maintainer'] = 'testsysadmin'
                if not data_dict.get('maintainer_email'):
                    data_dict['maintainer_email'] = 'test@test.org'
                if not private:
                    if not data_dict.get('data_update_frequency'):
                        data_dict['data_update_frequency'] = '0'
                    if not data_dict.get('dataset_date'):
                        data_dict['dataset_date'] = '[2011-11-11 TO 2011-11-11]'
                    if not data_dict.get('methodology'):
                        data_dict['methodology'] = 'Automatically inserted test methodology'
            return original_package_create(context, data_dict)
        logic._actions['package_create'] = package_create_wrapper

    @classmethod
    def get_backwards_compatible_test_client(cls):
        return HDXBackwardsCompatibleTestClient(cls.app.app, helpers.CKANResponse)


class HdxFunctionalBaseTest(HdxBaseTest):

    '''A base class for functional testing that loads all hdx_* extensions.'''

    @classmethod
    def _load_plugins(cls):
        load_plugin('hdx_service_checker hdx_crisis hdx_search sitemap hdx_org_group hdx_group hdx_package hdx_user_extra hdx_mail_validate hdx_users hdx_theme requestdata showcase')


class HDXBackwardsCompatibleTestClient(helpers.CKANTestClient):

    def __init__(self, application, response_wrapper=None, use_cookies=True, allow_subdomain_redirects=False):
        super(HDXBackwardsCompatibleTestClient, self).__init__(application, response_wrapper, use_cookies,
                                                               allow_subdomain_redirects)

    def post(self, *args, **kwargs):
        params = kwargs.pop("params", None)
        if params:
            kwargs["data"] = params
        return super(HDXBackwardsCompatibleTestClient, self).post(*args, **kwargs)

    def open(self, *args, **kwargs):
        kwargs['follow_redirects'] = False
        return super(HDXBackwardsCompatibleTestClient, self).open(*args, **kwargs)
