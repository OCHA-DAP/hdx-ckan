import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_theme.tests.hdx_test_with_inds_and_orgs as hdx_test_with_inds_and_orgs


class OrgGroupBaseTest(hdx_test_base.HdxBaseTest):

    @classmethod
    def _create_test_data(cls):
        import ckanext.ytp.request.model as ytp_model
        ytp_model.setup()
        super(OrgGroupBaseTest, cls)._create_test_data()

class OrgGroupBaseWithIndsAndOrgsTest(hdx_test_with_inds_and_orgs.HDXWithIndsAndOrgsTest):

    @classmethod
    def _create_test_data(cls, create_datasets=True, create_members=False):
        import ckanext.ytp.request.model as ytp_model
        ytp_model.setup()
        super(OrgGroupBaseWithIndsAndOrgsTest, cls)._create_test_data(create_datasets, create_members)
