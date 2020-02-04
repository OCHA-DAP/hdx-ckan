import os
import logging

import ckan.lib.munge as munge
from ckan.lib import uploader

from ckanext.s3filestore.uploader import S3ResourceUploader

from ckanext.hdx_theme.helpers.config import is_s3filestore_enabled

log = logging.getLogger(__name__)


def file_remove(resource_id, resource_name, resource_url_type):

    def file_remove_local(resource_id):
        id = resource_id
        storage_path = uploader.get_storage_path()
        directory = os.path.join(storage_path, 'resources', id[0:3], id[3:6])
        filepath = os.path.join(directory, id[6:])

        # remove file and its directory tree
        try:
            # remove file
            os.remove(filepath)
            # remove empty parent directories
            os.removedirs(directory)
            log.info(u'File %s is deleted.' % filepath)
        except OSError, e:
            log.debug(u'Error: %s - %s.' % (e.filename, e.strerror))

        pass

    def file_remove_s3(resource_id, resource_name):
        try:
            uploader = S3ResourceUploader({})
            munged_resource_name = munge.munge_filename(resource_name)
            filepath = uploader.get_path(resource_id, munged_resource_name)
            uploader.clear_key(filepath)
        except Exception, e:
            msg = 'Couldn\'t delete file from S3'
            log.warning(msg + str(e))

    if resource_url_type == 'upload':
        if is_s3filestore_enabled():
            file_remove_s3(resource_id, resource_name)
        else:
            file_remove_local(resource_id)
