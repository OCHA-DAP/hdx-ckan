import pytest
from click.testing import CliRunner
import ckanext.hdx_pages.model as pages_model
from ckanext.hdx_pages import command


class DummyModel:
    def __init__(self):
        self.called = []

    def create_table(self):
        self.called.append("create_table")

    def delete_table(self):
        self.called.append("delete_table")

    def drop_table(self):
        self.called.append("drop_table")


@pytest.fixture
def dummy_model(monkeypatch):
    dm = DummyModel()
    monkeypatch.setattr(pages_model, "create_table", dm.create_table)
    monkeypatch.setattr(pages_model, "delete_table", dm.delete_table)
    monkeypatch.setattr(pages_model, 'drop_table', dm.drop_table)
    return dm


def test_initdb_calls_create_table(dummy_model):
    runner = CliRunner()
    result = runner.invoke(command.initdb)
    assert result.exit_code == 0
    assert dummy_model.called == ["create_table"]


def test_cleandb_calls_delete_table(dummy_model):
    runner = CliRunner()
    result = runner.invoke(command.cleandb)
    assert result.exit_code == 0
    assert dummy_model.called == ["delete_table"]

def test_droptabledb_calls_drop_table(dummy_model):
    runner = CliRunner()
    result = runner.invoke(command.droptabledb)
    assert result.exit_code == 0
    assert dummy_model.called == ["drop_table"]
