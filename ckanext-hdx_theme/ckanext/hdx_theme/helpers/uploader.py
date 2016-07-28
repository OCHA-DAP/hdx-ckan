import os
import cgi

import pylons.config as config

import ckan.lib.uploader as uploader
import ckan.lib.munge as munge
import ckan.logic as logic


class GlobalUpload(object):
    '''
    This is heavily based on ckan.logic.uploader.ResourceUpload
    '''

    def __init__(self, file_dict):
        path = uploader.get_storage_path()
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
        self.filename = None

        upload_field_storage = file_dict.pop('upload', None)

        if isinstance(upload_field_storage, cgi.FieldStorage):
            self.filename = upload_field_storage.filename
            self.filename = munge.munge_filename(self.filename)
            file_dict['filename'] = self.filename
            self.upload_file = upload_field_storage.file

    def get_path(self, filename):
        filepath = os.path.join(self.get_directory(), filename)
        return filepath

    def get_directory(self):
        return self.storage_path

    def upload(self):

        max_size = config.get('ckan.max_image_size', 2)

        if not self.storage_path:
            raise GlobalUploadException("No storage_path")

        directory = self.get_directory()
        filepath = self.get_path(self.filename)

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


class GlobalUploadException(Exception):
    def __init__(self, message, exceptions):
        super(GlobalUploadException, self).__init__(message)

        self.errors = exceptions
