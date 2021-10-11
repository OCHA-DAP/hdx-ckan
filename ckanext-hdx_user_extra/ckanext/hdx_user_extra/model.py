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

from sqlalchemy.schema import Table, Column, ForeignKey, CreateTable, Index

mapper = orm.mapper
log = logging.getLogger(__name__)

user_extra_table = None

def setup():
    if user_extra_table is None:
        define_user_extra_table()
        log.debug('User extra table defined in memory')

    create_table()


class UserExtra(DomainObject):
    '''
    User extra information
    '''

    def __init__(self, user_id, key, value):
        self.user_id = user_id
        self.key = key
        self.value = value

    @staticmethod
    def get(user_id, key):
        '''

        :param user_id:
        :type user_id: str
        :param key:
        :type key: str
        :return:
        :rtype: UserExtra
        '''
        query = meta.Session.query(UserExtra)
        return query.filter_by(user_id=user_id, key=key).first()

    @staticmethod
    def get_by_user(user_id):
        '''
        :param user_id:
        :type user_id: str
        :return:
        :rtype: list of UserExtra
        '''
        query = meta.Session.query(UserExtra).filter_by(user_id=user_id)
        result = query.all()
        return result

    # @staticmethod
    # def get_by_key(key):
    #     query = meta.Session.query(UserExtra)
    #     return query.filter_by(key=key).all()

    @staticmethod
    def check_exists():
        return user_extra_table.exists()

    def as_dict(self):
        d = {k: v for k, v in vars(self).items() if not k.startswith('_')}
        return d



def define_user_extra_table():
    global user_extra_table
    user_extra_table = Table('user_extra', meta.metadata,
                             Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                             Column('user_id', types.UnicodeText, ForeignKey('user.id')),
                             Column('key', types.UnicodeText),
                             Column('value', types.UnicodeText),
                             )
    Index('user_id_key_idx', user_extra_table.c.user_id, user_extra_table.c.key, unique=True)
    mapper(UserExtra, user_extra_table, extension=[extension.PluginMapperExtension(), ])

#
# def _create_extra(key, value):
#     return UserExtra(key=unicode(key), value=value)


def create_table():
    '''
    Create user_extra table
    '''
    if model.user_table.exists() and not user_extra_table.exists():
        user_extra_table.create()
        log.debug('User extra table created')


def delete_table():
    '''
    Delete information from user_extra table
    '''
    print('User Extra trying to delete table...')
    if user_extra_table.exists():
        print('User Extra delete table...')
        user_extra_table.delete()
        log.debug('Validation Token table deleted')
        print('DONE User Extra delete table...')


def drop_table():
    '''
    Drop user_extra table
    '''
    print('User Extra trying to drop table...')
    if user_extra_table.exists():
        print('User Extra drop table...')
        user_extra_table.drop()
        log.debug('Validation Token table dropped')
        print('DONE User Extra drop table...')
