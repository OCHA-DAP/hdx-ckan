from ckanext.hdx_package.helpers.constants import DOCUMENTATION_LINKS, TABULAR_DATA_EXPLANATION_LINK


def test_documentation_links():
    assert DOCUMENTATION_LINKS['MAIN'] == 'https://docs.humdata.org/'
    assert DOCUMENTATION_LINKS['TABULAR_DATA_ENDPOINTS'] == 'https://docs.humdata.org/build/hdx-apis/tabular-data-endpoints'
    assert DOCUMENTATION_LINKS['TERMS_OF_SERVICE'] == 'https://docs.humdata.org/about/hdx-terms-of-service'
    assert DOCUMENTATION_LINKS['QA_PROCESS'] == 'https://docs.humdata.org/publish'
    assert DOCUMENTATION_LINKS['RESOURCES_FOR_DEVELOPERS'] == 'https://docs.humdata.org/build'
    assert DOCUMENTATION_LINKS['DATA_LICENSES'] == 'https://docs.humdata.org/about/data-licenses'


def test_tabular_data_explanation_link():
    assert TABULAR_DATA_EXPLANATION_LINK == DOCUMENTATION_LINKS['TABULAR_DATA_ENDPOINTS']
