from datetime import datetime

import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

from ckanext.hdx_org_group.tests.test_data_completeness import _generate_dataset_dict
from ckanext.hdx_pages.tests import LOCATION, ORG

h = tk.h
ValidationError = tk.ValidationError


@pytest.mark.usefixtures("hdx_clean_db", "with_request_context")
class TestActivityStream(object):

    def test_hdx_package_ajax_activity_stream(self, app):
        USER = 'test_sysadmin_activity_stream_user'
        user = factories.User(name=USER, sysadmin=True)
        group = factories.Group(name=LOCATION)
        org = factories.Organization(
            name=ORG,
            title='ORG NAME FOR ACTIVITY STREAM',
            users=[
                {'name': USER, 'capacity': 'editor'},
            ],
            hdx_org_type='donor',
            org_url='https://hdx.hdxtest.org/'
        )
        package = _generate_dataset_dict('dataset1-activity-stream', ORG, LOCATION, datetime.now(), user.get('id'))

        # Update the package
        package['notes'] = 'Updated description'
        tk.get_action('package_update')({'user': 'test_sysadmin_activity_stream_user'}, package)

        # Get activity stream HTML
        activity_stream = tk.get_action('hdx_package_activity_stream')({'user': 'test_sysadmin_activity_stream_user'}, {'id': package['id']})

        # Check if activity stream contains entries
        assert activity_stream is not None
        assert '"c-activity-stream"' in activity_stream
        assert 'created the dataset' in activity_stream
        assert 'updated the dataset' in activity_stream
