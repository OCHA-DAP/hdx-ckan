import ckan.plugins.toolkit as tk
from ckan.types import Context

from ckanext.hdx_search.actions.authorize import hdx_qa_dashboard_show
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class TestHdxQaDashboardShow(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):
    def test_qa_dashboard_show_returns_failure(self):
        """Test that hdx_qa_dashboard_show returns failure response"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert result['success'] is False
        assert 'msg' in result
        assert 'sysadmins' in result['msg'].lower() or 'qa officers' in result['msg'].lower()

    def test_qa_dashboard_show_with_empty_context(self):
        """Test hdx_qa_dashboard_show with empty context"""
        context: Context = {}
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert result['success'] is False
        assert 'msg' in result

    def test_qa_dashboard_show_with_empty_data_dict(self):
        """Test hdx_qa_dashboard_show with empty data dictionary"""
        context: Context = {'ignore_auth': True, 'user': 'testuser'}
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert result['success'] is False
        assert 'msg' in result

    def test_qa_dashboard_show_with_sysadmin_context(self):
        """Test hdx_qa_dashboard_show still returns failure even with sysadmin"""
        context: Context = {
            'ignore_auth': True,
            'user': 'testsysadmin',
            'auth_user_obj': tk.get_action('user_show')({}, {'id': 'testsysadmin'}),
        }
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert result['success'] is False
        assert 'msg' in result

    def test_qa_dashboard_show_response_structure(self):
        """Test that response has correct structure"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert isinstance(result, dict)
        assert 'success' in result
        assert 'msg' in result
        assert isinstance(result['success'], bool)
        assert isinstance(result['msg'], str)

    def test_qa_dashboard_show_message_content(self):
        """Test that error message is meaningful"""
        context: Context = {'ignore_auth': True}
        data_dict = {}

        result = hdx_qa_dashboard_show(context, data_dict)

        msg = result['msg']
        assert len(msg) > 0
        assert 'qa' in msg.lower() or 'dashboard' in msg.lower()

    def test_qa_dashboard_show_with_various_users(self):
        """Test hdx_qa_dashboard_show with different user types"""
        users = ['testsysadmin', 'tester', 'annafan']

        for user_name in users:
            context: Context = {'ignore_auth': True, 'user': user_name}
            data_dict = {}

            result = hdx_qa_dashboard_show(context, data_dict)

            assert result['success'] is False
            assert 'msg' in result

    def test_qa_dashboard_show_with_additional_data(self):
        """Test hdx_qa_dashboard_show ignores additional data_dict parameters"""
        context: Context = {'ignore_auth': True}
        data_dict = {'user_id': 'test_user', 'organization_id': 'test_org', 'extra_param': 'extra_value'}

        result = hdx_qa_dashboard_show(context, data_dict)

        assert result['success'] is False
        assert 'msg' in result
