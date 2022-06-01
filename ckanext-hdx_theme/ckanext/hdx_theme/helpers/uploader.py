import os
import cgi
import logging

from werkzeug.datastructures import FileStorage as FlaskFileStorage

import ckan.lib.uploader as uploader
import ckan.lib.munge as munge
import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.exception import BaseHdxException

log = logging.getLogger(__name__)
config = tk.config
asint = tk.asint

ALLOWED_UPLOAD_TYPES = (cgi.FieldStorage, FlaskFileStorage)


def get_base_path():
    path = uploader.get_storage_path()
    return path


class GlobalUpload(object):
    '''
    This is heavily based on ckan.logic.uploader.ResourceUpload
    '''

    def __init__(self, file_dict):
        path = get_base_path()
        if not path:
            self.storage_path = None
            return
        self.storage_path = os.path.join(path, 'global')
        try:
            os.makedirs(self.storage_path)
        except OSError as e:
            # errno 17 is file already exists
            if e.errno != 17:
                raise
        self.filename = os.path.basename(file_dict.get('filename')) if file_dict.get('filename') else None

        upload_field_storage = file_dict.pop('upload', None)

        if isinstance(upload_field_storage, ALLOWED_UPLOAD_TYPES):
            self._update_filename(upload_field_storage)
            self.filename = munge.munge_filename(self.filename)
            file_dict['filename'] = self.filename
            self.upload_file = upload_field_storage.stream if isinstance(upload_field_storage, FlaskFileStorage) \
                else upload_field_storage.file

    def _update_filename(self, upload_field_storage):
        '''
        If self.filename was specified in constructor but has no extension, try to take it from the uploaded file info
        :param upload_field_storage:
        '''
        if self.filename:
            splitted = os.path.splitext(self.filename)

            if not splitted[1]:  # If there is no extension
                self.filename += os.path.splitext(upload_field_storage.filename)[1]
        else:
            self.filename = upload_field_storage.filename

    def get_path(self):
        filepath = os.path.join(self.get_directory(), self.filename)
        return filepath

    def get_directory(self):
        return self.storage_path

    def upload(self):

        max_size = asint(config.get('ckan.max_image_size', 2))

        if not self.storage_path:
            raise GlobalUploadException("No storage_path")

        directory = self.get_directory()
        filepath = self.get_path()

        # If a filename has been provided (a file is being uploaded)
        # we write it to the filepath (and overwrite it if it already
        # exists). This way the uploaded file will always be stored
        # in the same location
        if self.filename:
            try:
                os.makedirs(directory)
            except OSError as e:
                # errno 17 is file already exists
                if e.errno != 17:
                    raise
            tmp_filepath = filepath + '~'
            output_file = open(tmp_filepath, 'wb+')
            self.upload_file.seek(0)
            current_size = 0
            while True:
                current_size = current_size + 1
                # MB chunks
                data = self.upload_file.read(2 ** 20)
                if not data:
                    break
                output_file.write(data)
                if current_size > max_size:
                    os.remove(tmp_filepath)
                    raise GlobalUploadException('File upload too large')
            output_file.close()
            os.rename(tmp_filepath, filepath)
            return

    def delete(self):
        try:
            os.remove(self.get_path())
        except OSError as e:
            log.error("Unable to remove global file {}".format(self.get_path()))


class GlobalUploadException(BaseHdxException):
    pass
