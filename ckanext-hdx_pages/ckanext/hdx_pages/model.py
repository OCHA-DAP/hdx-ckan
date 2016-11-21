import sqlalchemy.orm as orm
import sqlalchemy.types as types
import logging
import datetime
import ckan.model as model
from ckan.model.domain_object import DomainObject
from ckan.model import meta, extension
import ckan.model.types as _types

from sqlalchemy.schema import Table, Column, ForeignKey, CreateTable, Index

mapper = orm.mapper
log = logging.getLogger(__name__)


class PageBaseModel(DomainObject):
    @classmethod
    def filter(cls, **kwargs):
        return meta.Session.query(cls).filter_by(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        instance = cls.filter(**kwargs).first()
        return instance

    @classmethod
    def count(cls):
        return meta.Session.query(cls).count()

    @classmethod
    def exists(cls, **kwargs):
        if cls.filter(**kwargs).first():
            return True
        else:
            return False

    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        meta.Session.add(instance)
        meta.Session.commit()
        return instance.as_dict()


class Page(PageBaseModel):
    '''
    Page table
    '''

    def __init__(self, name, title, description, type, state, sections, status, modified=None):
        self.name = name
        self.title = title
        self.description = description
        self.type = type
        self.state = state
        self.sections = sections
        self.status = status
        self.modified = modified

    @classmethod
    def get_by_id(cls, id):
        '''Returns a group object referenced by its id or name.'''
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
    def check_exists(self):
        return page_table.exists()


page_table = Table('page', meta.metadata,
                   Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                   Column('name', types.UnicodeText, nullable=False, unique=True, index=True),
                   Column('title', types.UnicodeText, nullable=False),
                   Column('description', types.UnicodeText, nullable=True),
                   Column('type', types.UnicodeText),
                   Column('state', types.UnicodeText),
                   Column('sections', types.UnicodeText),
                   Column('modified', types.DateTime, default=datetime.datetime.now, nullable=False),
                   Column('status', types.UnicodeText),
                   )

mapper(Page, page_table, extension=[extension.PluginMapperExtension(), ])


class PageGroupAssociation(PageBaseModel):
    @classmethod
    def get_group_ids_for_page(cls, page_id):
        '''
        Return a list of group ids associated with the passed page_id.
        '''
        associated_group_id_list = meta.Session.query(cls.group_id).filter_by(page_id=page_id).all()
        result = [res[0] for res in associated_group_id_list]
        return result


page_group_association_table = Table(
    'page_group_association',
    meta.metadata,
    Column('group_id', types.UnicodeText,
           ForeignKey('group.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False),
    Column('page_id', types.UnicodeText,
           ForeignKey('page.id', ondelete='CASCADE', onupdate='CASCADE'), primary_key=True, nullable=False)
)

meta.mapper(PageGroupAssociation, page_group_association_table)


def create_table():
    if not page_table.exists():
        page_table.create()
        print 'Page table created'
    if not page_group_association_table.exists():
        page_group_association_table.create()
        print "page group association table created"


def delete_table():
    if page_table.exists():
        page_table.delete()
        log.debug('Page table deleted')


def patch_table():
    if page_table.exists():
        try:
            print 'Starting to patch table'
            model.Session.connection().execute('''alter table page add column status text''')
            model.Session.commit()
            print 'Finish to patch table'
        except Exception as e:
            print "There was an error during patching page table: " + str(e.message)

    else:
        print 'page table not exist'


def drop_table():
    '''
    Drop page table
    '''
    if page_table.exists():
        page_table.drop()
        log.debug('Page table dropped')
