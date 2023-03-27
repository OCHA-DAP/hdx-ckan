import logging
from dataclasses import dataclass, asdict
from datetime import datetime

from typing import Set, Dict

log = logging.getLogger(__name__)

EVENT_TYPE_DATASET_CREATED = 'dataset-created'
EVENT_TYPE_DATASET_METADATA_CHANGED = 'dataset-metadata-changed'

EVENT_TYPE_RESOURCE_DELETED = 'resource-deleted'
EVENT_TYPE_RESOURCE_CREATED = 'resource-created'
EVENT_TYPE_RESOURCE_DATA_CHANGED = 'resource-data-changed'
EVENT_TYPE_RESOURCE_METADATA_CHANGED = 'resource-metadata-changed'


@dataclass
class Event(object):
    event_type: str
    event_time: str
    # initiator_user_id: str
    initiator_user_name: str


@dataclass
class DatasetEvent(Event):
    dataset_name: str
    dataset_id: str
    changed_fields: [dict]


@dataclass
class ResourceEvent(Event):
    dataset_name: str
    dataset_id: str
    changed_fields: [dict]
    resource_name: str
    resource_id: str


def detect_version_changes(username: str, old_dataset_dict: dict, new_dataset_dict: dict):
    detector = DatasetChangeDetector(username, old_dataset_dict, new_dataset_dict)
    detector.detect_changes()
    for event in detector.change_events:
        log.info('Event: {}'.format(event))

    event_list = [asdict(e) for e in detector.change_events]



class DatasetChangeDetector(object):

    FIELDS = {
        'name', 'title', 'notes', 'subnational', 'dataset_source', 'owner_org', 'dataset_date',
        'data_update_frequency', 'data_update_frequency', 'license_id', 'license_other',
        'methodology', 'methodology_other', 'caveats', 'archived', 'is_requestdata_type',
    }

    def __init__(self, username: str, old_dataset_dict: dict, new_dataset_dict: dict) -> None:
        super().__init__()
        self.change_events: [Event] = []
        self.timestamp = datetime.utcnow().isoformat()
        self.username = username
        self.old_dataset_dict = old_dataset_dict
        self.new_dataset_dict = new_dataset_dict

        self.dataset_id = new_dataset_dict['id']
        self.dataset_name = new_dataset_dict['name']

        self.old_resources_map = {r['id']:r for r in old_dataset_dict.get('resources', [])}
        self.new_resources_map = {r['id']:r for r in new_dataset_dict.get('resources', [])}

        self.deleted_resource_ids = self.old_resources_map.keys() - self.new_resources_map.keys()
        self.created_resource_ids = self.new_resources_map.keys() - self.old_resources_map.keys()
        self.common_resource_ids = set(self.old_resources_map.keys()).intersection(self.new_resources_map.keys())

    def detect_changes(self):
        self._detect_created_dataset()
        self._detect_metadata_changed_dataset()
        self._detect_deleted_resources()
        self._detect_created_resources()
        self._detect_changed_resources()

    def create_event_dict(self, event_name, **kwargs):
        event_dict = {
            'event_type': event_name,
            'event_time': self.timestamp,
            'initiator_user_name': self.username,
            'dataset_name': self.dataset_name,
            'dataset_id': self.dataset_id,
        }
        for k,v in kwargs.items():
            event_dict[k] = v
        return event_dict

    def append_event(self, event: Event):
        self.change_events.append(event)

    def _detect_created_dataset(self):
        if not self.old_dataset_dict:
            event_dict = self.create_event_dict(EVENT_TYPE_DATASET_CREATED, changed_fields=None)
            self.append_event(DatasetEvent(**event_dict))

    def _detect_metadata_changed_dataset(self):
        if self.old_dataset_dict:
            changes = _find_dict_changes(self.old_dataset_dict, self.new_dataset_dict, self.FIELDS)
            if changes:
                list_of_changes = list(changes.values())
                event_dict = self.create_event_dict(EVENT_TYPE_DATASET_METADATA_CHANGED, changed_fields=list_of_changes)
                self.append_event(DatasetEvent(**event_dict))

    def _detect_deleted_resources(self):
        for resource_id in self.deleted_resource_ids:
            resource_name = self.old_resources_map[resource_id]['name']
            event_dict = self.create_event_dict(
                EVENT_TYPE_RESOURCE_DELETED,
                resource_name=resource_name,
                resource_id=resource_id,
                changed_fields=None,
            )

            self.append_event(ResourceEvent(**event_dict))

    def _detect_created_resources(self):
        for resource_id in self.created_resource_ids:
            resource_name = self.new_resources_map[resource_id]['name']
            event_dict = self.create_event_dict(
                EVENT_TYPE_RESOURCE_CREATED,
                resource_name=resource_name,
                resource_id=resource_id,
                changed_fields=None,
            )
            self.append_event(ResourceEvent(**event_dict))

    def _detect_changed_resources(self):
        for resource_id in self.common_resource_ids:
            old_resource = self.old_resources_map[resource_id]
            new_resource = self.new_resources_map[resource_id]
            ResourceChangeDetector(self, old_resource, new_resource).detect_changes()


class ResourceChangeDetector(object):

    FIELDS = {'name', 'format', 'description', 'microdata', 'resource_type', 'url'}

    def __init__(self, dataset_detector:DatasetChangeDetector, old_resource: dict, new_resource:dict) -> None:
        super().__init__()
        self.dataset_detector = dataset_detector
        self.old_resource = old_resource
        self.new_resource = new_resource
        self.resource_id = new_resource['id']
        self.resource_name = new_resource['name']

    def create_event_dict(self, event_name, **kwargs) -> dict:
        event_dict = self.dataset_detector.create_event_dict(event_name, **kwargs)
        event_dict['resource_id'] = self.resource_id
        event_dict['resource_name'] = self.resource_name
        return event_dict

    def append_event(self, event: Event):
        self.dataset_detector.append_event(event)

    def detect_changes(self):
        self._detect_data_modified()
        self._detect_metadata_changed()

    def _detect_data_modified(self):
        key = 'last_modified'
        if self.old_resource[key] != self.new_resource[key]:
            event_dict = self.create_event_dict(EVENT_TYPE_RESOURCE_DATA_CHANGED, changed_fields=None)
            self.append_event(ResourceEvent(**event_dict))

    def _detect_metadata_changed(self):
        changes = _find_dict_changes(self.old_resource, self.new_resource, self.FIELDS)
        if changes:
            list_of_changes = list(changes.values())
            event_dict = self.create_event_dict(EVENT_TYPE_RESOURCE_METADATA_CHANGED, changed_fields=list_of_changes)
            self.append_event(ResourceEvent(**event_dict))


def _find_dict_changes(old_dict: dict, new_dict: dict, fields: Set[str] = None) -> Dict[str, dict]:
    if not fields:
        fields = set().union(old_dict.keys()).union(new_dict.keys())
    changes: Dict[str:dict] = {}
    for field in fields:
        old_value = old_dict.get(field)
        new_value = new_dict.get(field)
        if old_value != new_value:
            changes[field] = {
                'field': field,
                'new_value': new_value,
                'old_value': old_value,
            }
    return changes

