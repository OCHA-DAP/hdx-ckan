'''
Created on July 2nd, 2015

@author: dan
'''

import sqlalchemy.orm as orm
import sqlalchemy.types as types
import logging
import ckan.model as model
from ckan.model.domain_object import DomainObject
from ckan.model import meta, extension
import ckan.model.types as _types

from sqlalchemy.schema import Table, Column, ForeignKey, CreateTable

mapper = orm.mapper
log = logging.getLogger(__name__)


class UserExtra(DomainObject):
    '''
    User extra information
    '''

    def __init__(self, user_id, key, value):
        self.user_id = user_id
        self.key = key
        self.value = value

    @classmethod
    def get(self, user_id, key):
        query = meta.Session.query(UserExtra)
        return query.filter_by(user_id=user_id, key=key).first()

    @classmethod
    def get_by_user(self, user_id):
        query = meta.Session.query(UserExtra)
        return query.filter_by(user_id=user_id).all()

    @classmethod
    def get_by_key(self, key):
        query = meta.Session.query(UserExtra)
        return query.filter_by(key=key).all()

    @classmethod
    def check_exists(self):
        return user_extra_table.exists()


user_extra_table = Table('user_extra', meta.metadata,
                         Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                         Column('user_id', types.UnicodeText, ForeignKey('user.id')),
                         Column('key', types.UnicodeText),
                         Column('value', types.UnicodeText),
                         )

mapper(UserExtra, user_extra_table, extension=[extension.PluginMapperExtension(), ])


def _create_extra(key, value):
    return UserExtra(key=unicode(key), value=value)


def create_table():
    '''
    Create user_extra table
    '''
    print 'User Extra create table...'
    if model.user_table.exists() and not user_extra_table.exists():
        print CreateTable(user_extra_table)
        user_extra_table.create()
        print 'DONE validation_token_table.create()'
    print 'DONE User Model setup...'


def delete_table():
    '''
    Delete information from user_extra table
    '''
    print 'User Extra trying to delete table...'
    if user_extra_table.exists():
        print 'User Extra delete table...'
        user_extra_table.delete()
        log.debug('Validation Token table deleted')
        print 'DONE User Extra delete table...'


def drop_table():
    '''
    Drop user_extra table
    '''
    print 'User Extra trying to drop table...'
    if user_extra_table.exists():
        print 'User Extra drop table...'
        user_extra_table.drop()
        log.debug('Validation Token table dropped')
        print 'DONE User Extra drop table...'
