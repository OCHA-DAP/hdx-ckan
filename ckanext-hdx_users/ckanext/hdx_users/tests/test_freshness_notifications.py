import datetime

import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs

from ckanext.hdx_users.helpers.notifications import FreshnessNotificationsChecker
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_FREQ_INFO


class TestFreshnessNotifications(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    def test_notification_data_save(self):
        checker2 = FreshnessNotificationsChecker('tester')
        date1 = datetime.datetime.utcnow()
        checker2.set_dashboard_viewed(date1)
        assert checker2.get_dashboard_viewed() == date1

        checker2 = FreshnessNotificationsChecker('tester')
        date2 = date1 + datetime.timedelta(hours=1)
        checker2.set_dashboard_viewed(date2)
        assert checker2.get_dashboard_viewed() == date2

    def test_freshness_notification(self):
        data_update_frequency = 30
        days_in_the_past = data_update_frequency + UPDATE_FREQ_INFO[str(data_update_frequency)] + 1
        review_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_in_the_past)
        tester_user = model.User.by_name('tester')
        dataset = {
            'package_creator': 'test function',
            'private': False,
            'dataset_date': '01/01/1960-12/31/2012',
            'caveats': 'These are the caveats',
            'license_other': 'TEST OTHER LICENSE',
            'methodology': 'This is a test methodology',
            'dataset_source': 'World Bank',
            'license_id': 'hdx-other',
            'name': 'test_freshness_dataset_1',
            'notes': 'This is a hdxtest dataset 1',
            'title': 'Freshness Test Dataset 1',
            'groups': [{'name': 'roger'}],
            'owner_org': 'hdx-test-org',
            'maintainer': tester_user.id,
            'review_date': review_date.isoformat(),
            'data_update_frequency': data_update_frequency

        }

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._get_action('package_create')(context, dataset)

        checker = FreshnessNotificationsChecker('tester')
        has_notification = checker.has_unseen_expired_datasets()
        assert has_notification

        checker.set_dashboard_viewed(datetime.datetime.utcnow())
        has_notification_after = checker.has_unseen_expired_datasets()
        assert not has_notification_after
