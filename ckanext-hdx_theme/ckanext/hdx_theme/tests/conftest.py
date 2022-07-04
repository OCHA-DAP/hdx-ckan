import pytest

from ckan import model as model


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True

