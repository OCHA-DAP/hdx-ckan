import pytest
import mock

from ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs import HDXWithIndsAndOrgsTest


@pytest.mark.ckan_config("hdx.analytics.track_api", "true")
@pytest.mark.ckan_config("hdx.analytics.track_api.exclude_browsers", "Chrome,Firefox,Safari,Edge,Internet Explorer,Opera,IE")
@pytest.mark.ckan_config("hdx.analytics.track_api.exclude_other", "A_Quick_Example,test,HDXINTERNAL")
class TestRobotApiCall(HDXWithIndsAndOrgsTest):

    DATASET_ID = 'test_dataset_1'

    @mock.patch('ckanext.hdx_theme.util.analytics_api._send_to_queue')
    def test_event_not_sent_for_controller(self, mocked_send_to_q):

        res = self.app.get('/dataset/{}'.format(self.DATASET_ID))
        call_count = mocked_send_to_q.call_count
        assert call_count == 0

    @mock.patch('ckanext.hdx_theme.util.analytics_api._send_to_queue')
    def test_event_sent_for_direct_api_call(self, mocked_send_to_q):
        res = self.app.get('/api/action/package_show?id={}'.format(self.DATASET_ID))
        call_count = mocked_send_to_q.call_count
        assert call_count == 1

    @mock.patch('ckanext.hdx_theme.util.analytics_api._send_to_queue')
    def test_event_not_sent_for_excluded_browser(self, mocked_send_to_q):
        firefox_ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:67.0) Gecko/20100101 Firefox/67.0'
        res = self.app.get('/api/action/package_show?id={}'.format(self.DATASET_ID),
                           headers={
                               'User-Agent': firefox_ua
                           })
        call_count = mocked_send_to_q.call_count
        assert call_count == 0
