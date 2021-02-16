
# https://github.com/okfn/ckanext-datahub/blob/release-v2.0/ckanext/datahub/model/user_extra.py

""" Provides extras for user model """

from sqlalchemy import orm, types, Column, Table, ForeignKey

import ckan.model.group as group
import ckan.model.meta as meta
import ckan.model.types as _types
import ckan.model.domain_object as domain_object

import logging
from ckan import model

log = logging.getLogger(__name__)

__all__ = ['MemberExtra', 'member_extra_table']

member_extra_table = None


class MemberExtra(domain_object.DomainObject):
    pass


def setup():
    global member_extra_table
    if member_extra_table is None:
        member_extra_table = Table('member_extra', meta.metadata,
                                   Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                                   Column('member_id', types.UnicodeText, ForeignKey('member.id')),
                                   Column('key', types.UnicodeText),
                                   Column('value', types.UnicodeText))

        meta.mapper(MemberExtra, member_extra_table,
                    properties={'member': orm.relation(group.Member, backref=orm.backref('extras',
                                                                                         cascade='all, delete, delete-orphan'))},
                    order_by=[member_extra_table.c.member_id, member_extra_table.c.key])

        # meta.mapper(group.Member, group.member_table, properties={
        #     'extras': orm.relationship(MemberExtra, order_by=member_extra_table.c.id)
        # })

    if model.member_table.exists() and not member_extra_table.exists():
        member_extra_table.create()
        log.debug('Member extra table created')


def _create_extra(key, value):
    return MemberExtra(key=unicode(key), value=value)

