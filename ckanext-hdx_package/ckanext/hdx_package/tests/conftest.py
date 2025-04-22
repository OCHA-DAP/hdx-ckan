import pytest
from ckanext.hdx_theme.tests.conftest import keep_db_tables_on_clean, dataset_with_uploaded_resource, \
    hdx_with_plugins, hdx_clean_db
from ckan import model as model

@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True
