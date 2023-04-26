import ckanext.hdx_package.helpers.resource_triggers.geopreview as geopreview
import ckanext.hdx_package.helpers.resource_triggers.fs_check as fs_check
import ckanext.hdx_package.helpers.resource_triggers.change_detection as change_detection

BEFORE_PACKAGE_UPDATE_LISTENERS = [
    geopreview._before_ckan_action,
    fs_check._before_ckan_action
]

AFTER_PACKAGE_UPDATE_LISTENERS = [
    geopreview._after_ckan_action,
    fs_check._after_ckan_action
]

VERSION_CHANGE_ACTIONS = [
    change_detection.detect_version_changes
]
