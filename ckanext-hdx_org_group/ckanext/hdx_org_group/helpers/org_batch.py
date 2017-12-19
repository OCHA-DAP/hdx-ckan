import logging
import datetime
import uuid

import ckan.logic as logic
import ckan.model as model

from pylons import config
from ckanext.hdx_org_group.model import OrganizationBatch

log = logging.getLogger(__name__)


def get_batch_or_generate(org_identifier):
    try:
        batch_id = get_batch(org_identifier)
        log.info('Batch id is ' + batch_id)
    except Exception, e:
        batch_id = 'MANUAL-' + unicode(uuid.uuid4())
        log.error(str(e))

    return batch_id


def get_batch(org_identifier):
    max_minutes = int(config.get('hdx.batch.period_in_mins', '30'))
    batch = None
    if not org_identifier:
        raise NoOrganization('organization_id needs to exist')

    group = model.Group.get(org_identifier)
    if not group:
        raise OrganizationNotFound('Organization {} not found in the database'.format(org_identifier))

    organization_id = group.id

    right_now = datetime.datetime.utcnow()

    organization_batch = OrganizationBatch._get_by_organization_id(organization_id, for_update=True)
    if not organization_batch:
        # organization batch doesn't exist
        organization_batch = OrganizationBatch(organization_id)
        organization_batch.save()
        batch = organization_batch.batch

    else:
        minutes = (right_now - organization_batch.last_modified).seconds / 60
        organization_batch.last_modified = right_now
        if minutes > max_minutes:
            organization_batch.batch = unicode(uuid.uuid4())
        organization_batch.save()
        batch = organization_batch.batch

    return batch


class NoOrganization(logic.ActionError):
    pass


class OrganizationNotFound(logic.ActionError):
    pass
