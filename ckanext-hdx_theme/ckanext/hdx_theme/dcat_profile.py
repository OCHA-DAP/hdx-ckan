import logging
import re

from rdflib import Literal

from ckan.plugins import toolkit
from ckantoolkit import url_for
from ckanext.dcat.profiles import SCHEMA
from ckanext.dcat.profiles.schemaorg import SchemaOrgProfile

log = logging.getLogger(__name__)

# Regex for UUID detection (maintainer field stores user IDs)
_UUID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE
)


def _resolve_maintainer_name(maintainer_value):
    """Resolve a maintainer value to a display name.
    """
    if not maintainer_value:
        return None
    if not _UUID_RE.match(maintainer_value):
        return maintainer_value
    try:
        user = toolkit.get_action('user_show')(
            {'ignore_auth': True}, {'id': maintainer_value}
        )
        return user.get('display_name') or user.get('fullname') or user.get('name')
    except Exception:
        return maintainer_value


def _parse_dataset_date(dataset_date):
    """Parse HDX dataset_date format into (start, end) ISO strings.

    Format: ``[2020-03-11T00:00:00 TO 2020-04-12T00:00:00]``
    Ongoing: ``[2020-03-11T00:00:00 TO *]``

    Returns a tuple ``(start_iso, end_iso)`` where either may be ``None``.
    """
    if not dataset_date:
        return None, None

    inner = dataset_date.strip('[]').strip()
    parts = inner.split(' TO ')
    if len(parts) != 2:
        return None, None

    start_raw = parts[0].strip()
    end_raw = parts[1].strip()

    start = start_raw if start_raw and start_raw != '*' else None
    end = end_raw if end_raw and end_raw != '*' else None

    return start, end


class HDXSchemaOrgProfile(SchemaOrgProfile):

    # Extension so we can add additional fields to the inline schema
    def additional_fields(self, dataset_ref, dataset_dict):
        is_private = dataset_dict.get('private', False)
        self.g.add((dataset_ref, SCHEMA.isAccessibleForFree, Literal(not is_private)))

    # identifier: use the HDX canonical URL as the dataset identifier
    def _basic_fields_graph(self, dataset_ref, dataset_dict):
        super()._basic_fields_graph(dataset_ref, dataset_dict)
        dataset_url = url_for('dataset.read', id=dataset_dict['name'], _external=True)
        self.g.add((dataset_ref, SCHEMA.identifier, Literal(dataset_url)))

    # ContactPoint: resolve maintainer UUID to display name
    # Example output: 
    # {
    #     "@id": "_:Ne6330a3db1c447919333218bcaf48c7c",
    #     "@type": "schema:ContactPoint",
    #     "schema:contactType": "customer service",
    #     "schema:name": "hdx",
    #     "schema:url": "https://data.humdata.local"
    # }
    def _agent_graph(self, dataset_ref, dataset_dict, agent_type, schema_property_prefix):
        """Override to resolve the maintainer UUID before the base class
        serialises it as the ContactPoint name."""

        maintainer = dataset_dict.get('maintainer')
        original_maintainer = maintainer
        if maintainer and _UUID_RE.match(maintainer):
            resolved = _resolve_maintainer_name(maintainer)
            if resolved:
                dataset_dict['maintainer'] = resolved

        try:
            super()._agent_graph(dataset_ref, dataset_dict, agent_type, schema_property_prefix)
        finally:
            # Restore so we don't mutate the dict for other consumers
            dataset_dict['maintainer'] = original_maintainer

        # sameAs on publisher Organization for entity disambiguation
        if schema_property_prefix == 'publisher':
            org = dataset_dict.get('organization')
            if org:
                org_url = self._get_org_url(org)
                if org_url:
                    for org_node in self.g.objects(dataset_ref, agent_type):
                        self.g.add((org_node, SCHEMA.sameAs, Literal(org_url)))
                        break

    def _get_org_url(self, org_dict):
        """Look up the org_url extra for an organization."""
        org_id = org_dict.get('id') or org_dict.get('name')
        if not org_id:
            return None
        try:
            full_org = toolkit.get_action('organization_show')(
                {'ignore_auth': True},
                {'id': org_id, 'include_datasets': False},
            )
            return full_org.get('org_url')
        except Exception:
            return None

    # spatialCoverage from HDX locations
    # Google accepts a simple text value, eg: "spatialCoverage": "Afghanistan"
    def _spatial_graph(self, dataset_ref, dataset_dict):
        groups = dataset_dict.get('groups', [])
        if not groups:
            return

        names = []
        for group in groups:
            display_name = (
                group.get('display_name') or group.get('title') or group.get('name')
            )
            if display_name:
                names.append(display_name)

        if names:
            self.g.add((
                dataset_ref,
                SCHEMA.spatialCoverage,
                Literal(', '.join(names)),
            ))

    # temporalCoverage from HDX dataset_date extra
    def _temporal_graph(self, dataset_ref, dataset_dict):
        dataset_date = self._get_dataset_value(dataset_dict, 'dataset_date')
        if not dataset_date:
            return

        start, end = _parse_dataset_date(dataset_date)
        if start and end:
            self.g.add((
                dataset_ref,
                SCHEMA.temporalCoverage,
                Literal('{}/{}'.format(start, end)),
            ))
        elif start:
            # Ongoing dataset —> open-ended interval
            self.g.add((
                dataset_ref,
                SCHEMA.temporalCoverage,
                Literal('{}/..'.format(start)),
            ))
        elif end:
            self._add_date_triple(dataset_ref, SCHEMA.temporalCoverage, end)
