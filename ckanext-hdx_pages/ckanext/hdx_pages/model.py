from __future__ import print_function

import datetime
import logging

import ckan.model as model
import ckan.model.types as _types
import sqlalchemy.orm as orm
import sqlalchemy.types as types
from ckan.model import meta
from ckan.model.domain_object import DomainObject
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.schema import Column, ForeignKey, Table

mapper = orm.mapper
log = logging.getLogger(__name__)

page_table = None
page_group_association_table = None
page_tag_association_table = None


def setup():
    if page_table is None:
        define_page_table()
        log.debug("Page table defined in memory")

    if page_group_association_table is None:
        define_page_group_association_table()
        log.debug("Page group association table defined in memory")

    if page_tag_association_table is None:
        define_page_tag_association_table()
        log.debug("Page tag association table defined in memory")

    # checks for existence first
    create_table()


class PageBaseModel(DomainObject):
    @classmethod
    def filter(cls, **kwargs):
        return meta.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        instance = cls.filter(**kwargs).first()
        return instance

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def create(cls, **kwargs):
        defer_commit = kwargs.get("defer_commit")
        if defer_commit:
            del kwargs["defer_commit"]
        instance = cls(**kwargs)
        meta.Session.add(instance)
        if not defer_commit:
            meta.Session.commit()
        return instance.as_dict()


class Page(PageBaseModel):
    """
    Page table
    """

    def __init__(
        self,
        name,
        title,
        description,
        type,
        state,
        sections,
        status,
        extras,
        modified=None,
    ):
        self.name = name
        self.title = title
        self.description = description
        self.type = type
        self.state = state
        self.sections = sections
        self.status = status
        self.extras = extras
        self.modified = modified

    @classmethod
    def get_by_id(cls, id):
        """Returns a group object referenced by its id or name."""
        query = meta.Session.query(cls).filter(cls.id == id)
        page = query.first()
        if page is None:
            page = cls.by_name(id)
        return page

    @classmethod
    def get_by_name(cls, name):
        query = meta.Session.query(cls)
        return query.filter_by(name=name).first()

    @classmethod
    def check_exists(cls):
        return page_table.exists()


def define_page_table():
    global page_table

    page_table = Table(
        "page",
        meta.metadata,
        Column(
            "id", types.UnicodeText, primary_key=True, default=_types.make_uuid
        ),
        Column(
            "name", types.UnicodeText, nullable=False, unique=True, index=True
        ),
        Column("title", types.UnicodeText, nullable=False),
        Column("description", types.UnicodeText, nullable=True),
        Column("type", types.UnicodeText),
        Column("state", types.UnicodeText),
        Column("sections", types.UnicodeText),
        Column("extras", types.UnicodeText),
        Column(
            "modified",
            types.DateTime,
            default=datetime.datetime.now,
            nullable=False,
        ),
        Column("status", types.UnicodeText),
    )

    mapper(Page, page_table)


class PageGroupAssociation(PageBaseModel):
    @classmethod
    def get_group_ids_for_page(cls, page_id):
        """
        Return a list of group ids associated with the passed page_id.
        """
        page = Page.get_by_id(page_id)
        # associated_group_id_list = meta.Session.query(cls.group_id).filter_by(page_id=page_id).all()

        result = [assoc.group_id for assoc in page.countries_assoc_all]
        return result


class PageTagAssociation(PageBaseModel):
    @classmethod
    def get_tag_ids_for_page(cls, page_id):
        """
        Return a list of tag ids associated with the passed page_id.
        """
        page = Page.get_by_id(page_id)

        result = [assoc.tag_id for assoc in page.tags_assoc_all]
        return result

    @classmethod
    def get_page_ids_for_tag(cls, tag_id):
        """
        Return a list of page ids associated with the passed tag_id.
        """

        page_tag_list = (
            meta.Session.query(cls.page_id).filter_by(tag_id=tag_id).all()
        )
        result = [res.page_id for res in page_tag_list]
        return result


def define_page_group_association_table():
    global page_group_association_table

    page_group_association_table = Table(
        "page_group_association",
        meta.metadata,
        Column(
            "group_id",
            types.UnicodeText,
            ForeignKey("group.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        Column(
            "page_id",
            types.UnicodeText,
            ForeignKey("page.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    meta.mapper(
        PageGroupAssociation,
        page_group_association_table,
        properties={
            "page": orm.relation(
                Page,
                backref=orm.backref(
                    "countries_assoc_all", cascade="all, delete-orphan"
                ),
            )
        },
    )


def define_page_tag_association_table():
    global page_tag_association_table

    page_tag_association_table = Table(
        "page_tag_association",
        meta.metadata,
        Column(
            "tag_id",
            types.UnicodeText,
            ForeignKey("tag.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        Column(
            "page_id",
            types.UnicodeText,
            ForeignKey("page.id", ondelete="CASCADE", onupdate="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    meta.mapper(
        PageTagAssociation,
        page_tag_association_table,
        properties={
            "page": orm.relation(
                Page,
                backref=orm.backref(
                    "tags_assoc_all", cascade="all, delete-orphan"
                ),
            )
        },
    )


def create_table():
    if model.group_table.exists():
        if not page_table.exists():
            page_table.create()
            print("Page table created")
        else:
            patch_table_add_column("extras")

        if not page_group_association_table.exists():
            page_group_association_table.create()
            print("page group association table created")
        if not page_tag_association_table.exists():
            page_tag_association_table.create()
            print("page tag association table created")


#
# def delete_table():
#     if page_table.exists():
#         page_table.delete()
#         log.debug('Page table deleted')
#
#
# def patch_table():
#     if page_table.exists():
#         try:
#             print 'Starting to patch table'
#             model.Session.connection().execute('''alter table page add column status text''')
#             model.Session.commit()
#             print 'Finish to patch table'
#         except Exception as e:
#             print "There was an error during patching page table: " + str(e.message)
#
#     else:
#         print 'page table not exist'
#
#
# def drop_table():
#     '''
#     Drop page table
#     '''
#     if page_table.exists():
#         page_table.drop()
#         log.debug('Page table dropped')


def patch_table_add_column(column_name):
    table_name = "page"
    try:
        # print('Starting to patch table %s' % table_name)
        engine = model.meta.engine
        inspector = Inspector.from_engine(engine)
        columns = inspector.get_columns(table_name)

        if not any(column["name"] == column_name for column in columns):
            column = Column(column_name, types.UnicodeText, default="")
            column_name = column.compile(dialect=engine.dialect)
            column_type = column.type.compile(engine.dialect)
            engine.execute(
                "ALTER TABLE %s ADD COLUMN %s %s"
                % (table_name, column_name, column_type)
            )

        # print('Finish to patch table %s' % table_name)
    except Exception:
        print(
            "There was an error during patching %s table. Column: %s"
            % (table_name, column_name)
        )
