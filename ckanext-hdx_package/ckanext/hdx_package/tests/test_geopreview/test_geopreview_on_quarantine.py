import mock
import ckan.plugins.toolkit as tk
import ckan.model as model
from ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs import HDXWithIndsAndOrgsTest

_get_action = tk.get_action
DATASET_NAME = 'test_dataset_1'
SYSADMIN_USER = 'testsysadmin'


class TestGeopreviewOnQuarantine(HDXWithIndsAndOrgsTest):

    @mock.patch('ckanext.hdx_package.actions.patch.delete_geopreview_layer')
    @mock.patch('ckanext.hdx_package.actions.patch.tag_s3_version_by_resource_id')
    def test_shape_info_removed_on_quarantine(self, tag_s3_mock, delete_geopreview_layer_mock):
        context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
        resource = {
            'url': tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/hdx_test.csv',
            'resource_type': 'file.upload',
            'format': 'SHP',
            'name': 'hdx_test1.shp.zip',
            'package_id': DATASET_NAME,
            'shape_info': 'This is a test shape info'
        }
        created_resource = _get_action('resource_create')(context, resource)
        assert 'shape_info' in created_resource

        quarantined_resource = _get_action('hdx_qa_resource_patch')(context, {
            'id': created_resource['id'],
            'in_quarantine': 'true',
        })
        assert quarantined_resource['in_quarantine'] is True
        assert 'shape_info' not in quarantined_resource

        assert delete_geopreview_layer_mock.call_count == 1
        assert delete_geopreview_layer_mock.call_args[0][0] == created_resource['id']



