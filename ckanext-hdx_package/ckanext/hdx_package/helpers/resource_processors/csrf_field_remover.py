from typing import Dict

from ckan.types import Context


def remove_unwanted_csrf_field(dataset_dict: Dict):
    resources = dataset_dict.get('resources')
    if resources:
        for resource_dict in resources:
            key = None
            for k in resource_dict.keys():
                if 'csrf' in k:
                    key = k
                    break
            if key:
                resource_dict.pop(key, None)

