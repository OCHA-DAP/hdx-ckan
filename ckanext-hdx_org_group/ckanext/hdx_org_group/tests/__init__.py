import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class OrgGroupBaseTest(hdx_test_base.HdxBaseTest):

    @classmethod
    def setup_class(cls):
        import ckanext.ytp.request.model as ytp_model
        super(OrgGroupBaseTest, cls).setup_class()
        ytp_model.setup()

class OrgGroupBaseWithIndsAndOrgsTest(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def setup_class(cls):
        import ckanext.ytp.request.model as ytp_model
        super(OrgGroupBaseWithIndsAndOrgsTest, cls).setup_class()
        ytp_model.setup()