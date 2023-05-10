import logging
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)
config = tk.config


def detect_version_changes(username: str, old_dataset_dict: dict, new_dataset_dict: dict):
    import requests
    import json
    url = config.get('hdx.change_detection.layer_url')

    if url:
        task_arguments = {
            'username': username,
            'old_dataset_dict': old_dataset_dict,
            'new_dataset_dict': new_dataset_dict,
        }

        response = requests.post(url, data=json.dumps(task_arguments), headers={'Content-type': 'application/json'})
        if response.status_code != 200:
            log.error('There was an error enqueueing the dataset {} for change detection: {}'.format(
                new_dataset_dict['name'], response.status_code
            ))
        response.raise_for_status()
        log.info('Response from enqueueing change detection for dataset {} is: {}. '.format(
            new_dataset_dict['name'], response.json().get('state')
        ))
    else:
        log.warning('No url configured change detection layer. This is probably ok in local envs or when running tests')

