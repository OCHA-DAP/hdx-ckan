import pytest
import os
from werkzeug.datastructures import FileStorage
import dateutil.parser as dateutil_parser

import ckan.tests.factories as factories
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

_get_action = tk.get_action
ValidationError = tk.ValidationError

STANDARD_USER = 'some_standard_user'
SYSADMIN_USER = 'sysadmin_user'
DATASET_NAME_UPLOADED_RESOURCE = 'dataset_name_for_resource_url_change_with_uploaded_resource'

LOCATION_NAME = 'some_location_for_resource_url_change'
ORG_NAME = 'org_name_for_resource_url_change'
RESOURCE_LINKED_URL = 'http://test.ckan.test/test.csv'

UPLOADED_RESOURCE = {
    'url': 'data1.csv',  # tk.config.get('ckan.site_url', '') + '/storage/f/test_folder/data1.csv',
    'resource_type': 'file.upload',
    'url_type': 'upload',
    'format': 'CSV',
    'name': 'data1.csv',
    'qa_hapi_report': 'initial string',
}


def _get_dataset_dict(external_resource: bool):
    dataset_name = DATASET_NAME_UPLOADED_RESOURCE
    resource = UPLOADED_RESOURCE
    return {
        "package_creator": "test function",
        "private": False,
        "dataset_date": "[1960-01-01 TO 2012-12-31]",
        "caveats": "These are the caveats",
        "license_other": "TEST OTHER LICENSE",
        "methodology": "This is a test methodology",
        "dataset_source": "Test data",
        "license_id": "hdx-other",
        "name": dataset_name,
        "notes": "This is a test dataset",
        "title": "Test Dataset " + dataset_name,
        "owner_org": ORG_NAME,
        "groups": [{"name": LOCATION_NAME}],
        "data_update_frequency": "30",
        "maintainer": STANDARD_USER,
        "resources": [
            resource
        ],
    }


#         user = model.User.by_name('sysadmin_user')
#         user.email = 'test@test.com'
#         model.Session.commit()
#         auth = {'Authorization': self.testsysadmin_token}
# testsysadmin_token = factories.APIToken(user='testsysadmin', expires_in=2, unit=60 * 60)['token']

@pytest.fixture()
def setup_data():
    factories.User(name=STANDARD_USER, email='some_standard_user@hdx.hdxtest.org')
    factories.User(name=SYSADMIN_USER, email='some_sysadmin@hdx.hdxtest.org', sysadmin=True)

    syadmin_obj = model.User.get('some_sysadmin@hdx.hdxtest.org')
    syadmin_obj.apikey = 'SYSADMIN_API_KEY'
    model.Session.commit()

    user_obj = model.User.get('some_standard_user@hdx.hdxtest.org')
    user_obj.apikey = 'USER_API_KEY'
    model.Session.commit()
    group = factories.Group(name=LOCATION_NAME)
    factories.Organization(
        name=ORG_NAME,
        title='ORG NAME FOR HDX_REL_URL',
        users=[
            {'name': STANDARD_USER, 'capacity': 'editor'},
        ],
        hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
        org_url='https://hdx.hdxtest.org/'
    )

    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    # external_dataset_dict = _get_action('package_create')(context, _get_dataset_dict(external_resource=True))
    uploaded_dataset_dict = _get_action('package_create')(context, _get_dataset_dict(external_resource=False))
    assert 'qa_hapi_report' not in uploaded_dataset_dict.get('resources')[0]

    context_sysadmin: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    package_dict = _get_action('package_show')(context, {'id': DATASET_NAME_UPLOADED_RESOURCE})


def _get_user_context():
    context: Context = {'model': model, 'session': model.Session, 'user': STANDARD_USER}
    return context


def _get_sysadmin_context():
    context: Context = {'model': model, 'session': model.Session, 'user': SYSADMIN_USER}
    return context


@pytest.mark.usefixtures("keep_db_tables_on_clean", "clean_db", "clean_index", "setup_data")
def test_last_modified_change_for_uploaded_resource():
    package_dict = _get_action('package_show')(_get_user_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})

    # try to update resource with qa_hapi_report as regular editor
    resource_dict_modified = _get_action('resource_patch')(_get_user_context(), {
        'id': package_dict['resources'][0]['id'],
        'description': 'new description',  # changing description
        'url': 'data1.csv',
        'name': 'data2.csv',  # changing the name
        'qa_hapi_report': 'regular user qa hapi report'
    })
    # qa_hapi_report not exist
    package_dict = _get_action('package_show')(_get_user_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
    assert 'qa_hapi_report' not in package_dict.get('resources')[0]
    # qa_hapi_report
    package_dict = _get_action('package_show')(_get_sysadmin_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
    assert 'qa_hapi_report' not in package_dict.get('resources')[0]

    # try to update resource with qa_hapi_report as sysadmin editor
    resource_dict_modified_hapi_report = _get_action('resource_patch')(_get_sysadmin_context(), {
        'id': package_dict['resources'][0]['id'],
        'description': 'new description',  # changing description
        'url': 'data1.csv',
        'name': 'data2.csv',  # changing the name
        'qa_hapi_report': 'sysadmin user qa hapi report'
    })
    # qa_hapi_report not displayed for regular user
    package_dict = _get_action('package_show')(_get_user_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
    assert 'qa_hapi_report' not in package_dict.get('resources')[0]

    # qa_hapi_report displays value for sysadmin only
    package_dict = _get_action('package_show')(_get_sysadmin_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
    assert 'qa_hapi_report' in package_dict.get('resources')[0]
    assert package_dict.get('resources')[0].get('qa_hapi_report') == 'sysadmin user qa hapi report'

    # qa_hapi_report will be removed/reset when upload
    res_id = package_dict['resources'][0]['id']
    file_path = os.path.join(os.path.dirname(__file__), 'data1.csv')
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        resource_dict = _get_action('resource_update')(_get_user_context(),
                                                       {
                                                           'id': res_id,
                                                           'name': 'data1.csv',
                                                           'url_type': 'upload',
                                                           'resource_type': 'file.upload',
                                                           'upload': file_upload,
                                                           'qa_hapi_report': 'updated user hapi report'

                                                       }
                                                       )
        package_dict = _get_action('package_show')(_get_user_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
        assert 'qa_hapi_report' not in package_dict.get('resources')[0]

        package_dict = _get_action('package_show')(_get_sysadmin_context(), {'id': DATASET_NAME_UPLOADED_RESOURCE})
        assert 'qa_hapi_report' not in package_dict.get('resources')[0]
