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


class Page(DomainObject):
    '''
    User extra information
    '''

    def __init__(self, name, title, description, type, state, sections, modified=None):
        self.name = name
        self.title = title
        self.description = description
        self.type = type
        self.state = state
        self.modified = modified
        self.sections = sections

    @classmethod
    def get(cls, id):
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
                   )

mapper(Page, page_table, extension=[extension.PluginMapperExtension(), ])


def create_table():
    if model.user_table.exists() and not page_table.exists():
        page_table.create()
        log.debug('Page table created')


def delete_table():
    if page_table.exists():
        page_table.delete()
        log.debug('Page table deleted')


def drop_table():
    '''
    Drop page table
    '''
    if page_table.exists():
        page_table.drop()
        log.debug('Page table dropped')
