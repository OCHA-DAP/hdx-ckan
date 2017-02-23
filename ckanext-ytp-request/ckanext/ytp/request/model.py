
# https://github.com/okfn/ckanext-datahub/blob/release-v2.0/ckanext/datahub/model/user_extra.py

""" Provides extras for user model """

import vdm.sqlalchemy
import vdm.sqlalchemy.stateful
from sqlalchemy import orm, types, Column, Table, ForeignKey

import ckan.model.group as group
import ckan.model.meta as meta
import ckan.model.types as _types
import ckan.model.domain_object as domain_object

import logging
from ckan import model
log = logging.getLogger(__name__)

__all__ = ['MemberExtra', 'member_extra_table']

member_extra_table = Table('member_extra', meta.metadata,
                           Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                           Column('member_id', types.UnicodeText, ForeignKey('member.id')),
                           Column('key', types.UnicodeText),
                           Column('value', types.UnicodeText))

vdm.sqlalchemy.make_table_stateful(member_extra_table)


class MemberExtra(vdm.sqlalchemy.StatefulObjectMixin, domain_object.DomainObject):
    pass


def setup():
    if model.member_table.exists() and not member_extra_table.exists():
        member_extra_table.create()
        log.debug('Member extra table created')


def _create_extra(key, value):
    return MemberExtra(key=unicode(key), value=value)


meta.mapper(MemberExtra, member_extra_table,
            properties={'member': orm.relation(group.Member, backref=orm.backref('_extras',
                                                                                 collection_class=orm.collections.attribute_mapped_collection(u'key'),
                                                                                 cascade='all, delete, delete-orphan'))},
            order_by=[member_extra_table.c.member_id, member_extra_table.c.key])

_extras_active = vdm.sqlalchemy.stateful.DeferredProperty('_extras', vdm.sqlalchemy.stateful.StatefulDict)
setattr(group.Member, 'extras_active', _extras_active)
group.Member.extras = vdm.sqlalchemy.stateful.OurAssociationProxy('extras_active', 'value', creator=_create_extra)
