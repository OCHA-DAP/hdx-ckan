import ckan.controllers.package as package_controller

from ckanext.hdx_package.helpers.analytics import resource_download_with_analytics
from ckanext.hdx_package.helpers.quarantine import resource_download_with_quarantine_check


before_download_functions = [resource_download_with_quarantine_check,resource_download_with_analytics]

def wrap_resource_download_function():
    '''
    Changes the original resource_download function from the package controller with a version that
    wraps the original function but also enqueues the tracking events
    '''
    original_resource_download = package_controller.PackageController.resource_download

    def new_resource_download(self, id, resource_id, filename=None):

        for f in before_download_functions:
            f(self, id, resource_id, filename)

        return original_resource_download(self, id, resource_id, filename)

    package_controller.PackageController.resource_download = new_resource_download
