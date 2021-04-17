import pytest
from lxml import etree

import ckan.lib.search as search
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as test_helpers
import ckanext.sitemap.tests.testdata as testdata

_get_action = tk.get_action
config = tk.config
url_for = tk.url_for
utf8_parser = etree.XMLParser(encoding='utf-8')
siteschema = etree.XMLSchema(etree.fromstring(testdata.sitemap.encode('utf-8'), parser=utf8_parser))
indexschema = etree.XMLSchema(etree.fromstring(testdata.sitemapindex.encode('utf-8'), parser=utf8_parser))


@pytest.mark.usefixtures("with_request_context")
class TestSitemap(object):

    dataset1_name = 'sitemap_test_dataset_1'
    dataset2_name = 'sitemap_test_dataset_2'

    dataset1_dict = None  # type: dict
    dataset2_dict = None  # type: dict

    @classmethod
    def setup_class(cls):
        search.clear_all()
        test_helpers.reset_db()
        cls.app = test_helpers._get_test_app()

        sysadmin = 'testsysadmin_sitemap'
        factories.Sysadmin(name=sysadmin)
        model.Session.commit()
        sysadmin_user = model.User.by_name(sysadmin)
        if sysadmin_user:
            sysadmin_user.email = sysadmin + '@test-domain.com'
            sysadmin_user.apikey = sysadmin + '_apikey'

        model.Session.commit()
        cls.sysadmin_user = {
            'name': sysadmin,
            'apikey': sysadmin_user.apikey
        }

        cls.dataset1_dict = cls._create_package(cls.dataset1_name, sysadmin)
        cls.dataset2_dict = cls._create_package(cls.dataset2_name, sysadmin, create_org_and_group=False)

    @classmethod
    def _create_package(cls, pkg_name, user, create_org_and_group=True):
        '''
        :param pkg_name: the name of the new package
        :type pkg_name: str
        :param create_org_and_group: whether to create the org and group for the package. Might've been created already.
        :type create_org_and_group: bool
        :return: id of newly created package
        :rtype: str
        '''
        if create_org_and_group:
            factories.Organization(name='test_owner_org',
                                   org_url='http://example.org/',
                                   hdx_org_type='academic_research',
                                   users=[{'name': 'testsysadmin', 'capacity': 'admin'}]
                                   )
            factories.Group(name='test_group1')
        package = {
            "package_creator": "test function",
            "private": False,
            "dataset_date": "[1960-01-01 TO 2012-12-31]",
            "caveats": "These are the caveats",
            "license_other": "TEST OTHER LICENSE",
            "methodology": "This is a test methodology",
            "dataset_source": "Test data",
            "license_id": "hdx-other",
            "name": pkg_name,
            "notes": "This is a test dataset",
            "title": "Test Dataset for QA Completed " + pkg_name,
            "owner_org": "test_owner_org",
            "groups": [{"name": "test_group1"}],
            "maintainer": user,
            "data_update_frequency": "0",
            "resources": [
                {
                    'package_id': pkg_name,
                    'url': config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
                    'resource_type': 'file.upload',
                    'format': 'CSV',
                    'name': 'hdx_test.csv',

                }
            ]
        }

        context = {'model': model, 'session': model.Session, 'user': user}
        package_dict = _get_action('package_create')(context, package)
        return package_dict

    def test_validity_index(self):
        url = url_for('sitemap.view')
        response = self.app.get(url)
        content_file = response.body
        assert indexschema.validate(etree.fromstring(content_file.encode('utf-8'), parser=utf8_parser))

    def test_validity_map(self):
        url = url_for('sitemap.index', page=1)
        response = self.app.get(url)
        content_file = response.body
        tree = etree.fromstring(content_file.encode('utf-8'), parser=utf8_parser)
        assert siteschema.validate(tree)

        assert self.dataset1_name in content_file
        assert self.dataset2_name in content_file

        # the datasets are fetched by default in desc order of the update time
        dataset2_url = config.get('ckan.site_url') + url_for('dataset.read', id=self.dataset2_name)
        assert tree[0][0].text == dataset2_url

        res_url = config.get('ckan.site_url') + url_for('resource.read',
                                                        id=self.dataset2_name,
                                                        resource_id=self.dataset2_dict['resources'][0]['id'])
        assert tree[1][0].text == res_url

        dataset2_date = self.dataset2_dict['metadata_modified'][:10]
        assert  tree[0][1].text == dataset2_date
