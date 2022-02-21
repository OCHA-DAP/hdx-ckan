import datetime
import logging

from sqlalchemy import types, Table, Column, ForeignKey, UniqueConstraint, Index, desc

import ckan.plugins.toolkit as tk

from ckan.model import meta, domain_object
from ckan.model import types as ckan_types

from ckan.model.user import user_table

log = logging.getLogger(__name__)
config = tk.config
asint = tk.asint

searched_string_table = None


def setup():
    if searched_string_table is None:
        define_searched_string_table()
        log.debug('Searched strings table defined in memory')


def create_table():
    if user_table.exists() and searched_string_table is not None and not searched_string_table.exists():
        searched_string_table.create()
        log.debug('Searched strings table created')


class SearchedString(domain_object.DomainObject):

    def __init__(self, search_string, user):
        self.search_string = search_string
        self.last_modified = datetime.datetime.utcnow()
        self.user = user

    def update_last_modified(self):
        self.last_modified = datetime.datetime.utcnow()

    @classmethod
    def latest_queries_for_user(cls, user_id):
        '''
        :param user_id:
        :type user_id: unicode
        :return:
        :rtype: list[SearchedString]
        '''

        hours_from_actual_search = asint(config.get('hdx.search_history.hours_from_actual_search', '24'))

        hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=hours_from_actual_search)
        query = meta.Session.query(cls).filter(cls.user == user_id).filter(cls.last_modified < hours_ago)\
            .order_by(desc(cls.last_modified)).limit(10)
        return query.all()

    @classmethod
    def by_search_string_and_user(cls, search_string, user_id):
        '''
        :param search_string:
        :type search_string: unicode
        :param user_id:
        :type user_id: unicode
        :return: the SearchedString object if found or None
        :rtype: SearchedString
        '''
        query = meta.Session.query(cls).filter(cls.search_string == search_string).filter(cls.user == user_id)
        result = query.first()
        return result


def define_searched_string_table():

    global searched_string_table

    searched_string_table = Table(
        'searched_string', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True,
               default=ckan_types.make_uuid),
        Column('last_modified', types.DateTime, default=datetime.datetime.utcnow),
        Column('user', types.UnicodeText, ForeignKey('user.id', ondelete='CASCADE', onupdate='CASCADE'),
               nullable=False, index=True),
        Column('search_string', types.UnicodeText, index=True),
        # Index('ix_searched_string_last_modified_desc', 'last_modified', postgresql_using='btree'),
        UniqueConstraint('search_string', 'user')
    )

    Index('ix_searched_string_last_modified_desc', searched_string_table.c.last_modified.desc())


    meta.mapper(SearchedString, searched_string_table)


