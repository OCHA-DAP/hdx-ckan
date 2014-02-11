from sqlalchemy.orm import object_session
from sqlalchemy import __version__ as sqav
from demo import *
from base import *

class TestMisc:
    @classmethod
    def teardown_class(self):
        repo.rebuild_db()

    def test_column_create(self):
        if sqav.startswith("0.6") or sqav.startswith("0.7"):
            ## FIXME???
            ## This test does not appear to test anything that is
            ## VDM specific. It also fails with SQLAlchemy 0.6
            ## Does this test really belong here?
            return
        
        tabxyz = Table('xyz', metadata,
            Column('id', Integer, primary_key=True)
            )
        col = Column('abc', Integer, ForeignKey('xyz.id'))
        # FK does *not* work
        assert len(col.foreign_keys) == 0
        tab = Table('tab', metadata,
            Column('abc', Integer, ForeignKey('xyz.id')),
            )
        col0 = tab.c['abc']
        fk0 = col0.foreign_keys[0]
        assert len(col0.foreign_keys) == 1
        assert fk0.parent is not None

        tab2 = Table('tab', metadata)
        tab2.append_column(
            Column('abc', Integer, ForeignKey('xyz.id'))
            )
        assert len(tab2.c['abc'].foreign_keys) == 1
        assert tab2.c['abc'].foreign_keys[0].parent is not None

        tab3 = Table('tab', metadata)
        col3 = col0.copy()
        col3.foreign_keys.add(tab.c['abc'].foreign_keys[0].copy())
        tab3.append_column(col3)
        assert len(tab3.c['abc'].foreign_keys) == 1
        # fails
        # assert tab3.c['abc'].foreign_keys[0].parent

        tab3 = Table('tab', metadata)
        col3 = col0.copy()
        tab3.append_column(col3)
        col3.foreign_keys.add(ForeignKey(col0.key)) 
        assert len(tab3.c['abc'].foreign_keys) == 1
        # fails
        # assert tab3.c['abc'].foreign_keys[0].parent
        tab4 = Table('tab', metadata)
        tab4.append_column(
            col0.copy()
            )
        tab4.c[col0.key].append_foreign_key(fk0.copy())
        assert len(tab4.c['abc'].foreign_keys) == 1
        assert tab4.c['abc'].foreign_keys[0].parent is not None

    def test_copy_column(self):
        t1 = package_table
        newtable = Table('mytable', metadata)
        copy_column('id', t1, newtable)
        outcol = newtable.c['id']
        assert outcol.name == 'id'
        assert outcol.primary_key == True
        # pick one with a fk
        name = 'license_id'
        copy_column(name, t1, newtable)
        incol = t1.c[name]
        outcol = newtable.c[name]
        assert outcol != incol
        assert outcol.key == incol.key
        assert len(incol.foreign_keys) == 1
        assert len(outcol.foreign_keys) == 1
        infk = list(incol.foreign_keys)[0]
        outfk = list(outcol.foreign_keys)[0]
        assert infk.parent is not None
        assert outfk.parent is not None

    def test_table_copy(self):
        t1 = package_table
        newtable = Table('newtable', metadata)
        copy_table(t1, newtable)
        assert len(newtable.c) == len(t1.c)
        # pick one with a fk
        incol = t1.c['license_id']
        outcol = None
        for col in newtable.c:
            if col.name == 'license_id':
                outcol = col
        assert outcol != incol
        assert outcol.key == incol.key
        assert len(incol.foreign_keys) == 1
        assert len(outcol.foreign_keys) == 1
        infk = list(incol.foreign_keys)[0]
        outfk = list(outcol.foreign_keys)[0]
        assert infk.parent is not None
        assert outfk.parent is not None

    def test_package_tag_table(self):
        col = package_tag_table.c['tag_id']
        assert len(col.foreign_keys) == 1

    def test_make_stateful(self):
        assert 'state' in package_table.c

    def test_make_revision_table(self):
        assert package_revision_table.name == 'package_revision'
        assert 'revision_id' in package_table.c
        assert 'state' in package_revision_table.c
        assert 'revision_id' in package_revision_table.c
        # very crude ...
        assert len(package_revision_table.c) == len(package_table.c) + 1
        # these tests may seem odd but they would incorporated following a bug
        # where this was *not* the case
        base = package_table
        rev = package_revision_table
        # crude (could be more specific about the fk)
        assert len(rev.c['revision_id'].foreign_keys) == 1
        assert rev.c['revision_id'].primary_key
        assert rev.c['id'].primary_key
        print rev.primary_key.columns
        assert len(rev.primary_key.columns) == 2

    def test_accessing_columns_on_object(self):
        table = class_mapper(Package).mapped_table
        print table.c.keys()
        assert len(table.c.keys()) > 0
        assert 'revision_id' in table.c.keys()

