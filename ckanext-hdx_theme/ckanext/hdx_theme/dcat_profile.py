import logging
import re

from rdflib import Literal

from ckan.plugins import toolkit
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
        self.g.add((dataset_ref, SCHEMA.isAccessibleForFree, Literal(True)))

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
