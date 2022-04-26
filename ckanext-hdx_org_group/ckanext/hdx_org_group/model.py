import datetime
import logging
import uuid

from sqlalchemy import types, Table, Column, ForeignKey
from six import text_type

from ckan.model import meta, domain_object
from ckan.model import types as ckan_types
from ckan.model.group import group_table

log = logging.getLogger(__name__)

organization_batch_table = None


def setup():
    if organization_batch_table is None:
        define_organization_batch_table()
        log.debug('Org batch table defined in memory')


def create_table():
    if group_table.exists() and organization_batch_table is not None and not organization_batch_table.exists():
        organization_batch_table.create()
        # print ('Org batch table created')


class OrganizationBatch(domain_object.DomainObject):

    def __init__(self, organization_id):
        self.organization = organization_id
        self.last_modified = datetime.datetime.utcnow()
        self.batch = text_type(uuid.uuid4())

    def _update_last_modified(self):
        self.last_modified = datetime.datetime.utcnow()

    @classmethod
    def _get_by_organization_id(cls, organization_id, for_update=False):
        '''
        :param organization_id:
        :type organization_id: text_type
        :param for_update:
        :type for_update: bool
        :return:
        :rtype: OrganizationBatch
        '''
        query = meta.Session.query(cls).filter(cls.organization == organization_id)
        if for_update:
            query = query.with_for_update()
        organization_batch = query.first()
        return organization_batch


def define_organization_batch_table():

    global organization_batch_table

    organization_batch_table = Table(
        'organization_batch', meta.metadata,
        Column('id', types.UnicodeText, primary_key=True,
               default=ckan_types.make_uuid),
        Column('last_modified', types.DateTime, default=datetime.datetime.utcnow),
        Column('organization', types.UnicodeText, ForeignKey('group.id', ondelete='CASCADE', onupdate='CASCADE'),
               unique=True, nullable=False, index=True),
        Column('batch', types.UnicodeText),
    )

    meta.mapper(OrganizationBatch, organization_batch_table)


