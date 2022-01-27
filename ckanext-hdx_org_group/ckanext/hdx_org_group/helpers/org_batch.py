import logging
import datetime
import uuid

from six import text_type

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_org_group.model import OrganizationBatch

log = logging.getLogger(__name__)

config = tk.config

BATCH_PERIOD_CONFIG = 'hdx.batch.period_in_mins'


def get_batch_or_generate(org_identifier):
    try:
        batch_id = get_batch(org_identifier)
        log.info('Batch id is ' + batch_id)
    except Exception as e:
        batch_id = 'MANUAL-' + text_type(uuid.uuid4())
        log.error(str(e))

    return batch_id


def get_batch(org_identifier):

    batch = None
    if not org_identifier:
        raise NoOrganization('organization_id needs to exist')

    group = model.Group.get(org_identifier)
    if not group:
        raise OrganizationNotFound('Organization {} not found in the database'.format(org_identifier))

    org_specific_period_config = '{}_{}'.format(BATCH_PERIOD_CONFIG, group.name)

    max_minutes = int(config.get(org_specific_period_config,
                                 config.get(BATCH_PERIOD_CONFIG, '3')))

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
            organization_batch.batch = text_type(uuid.uuid4())
        organization_batch.save()
        batch = organization_batch.batch

    return batch


class NoOrganization(logic.ActionError):
    pass


class OrganizationNotFound(logic.ActionError):
    pass
