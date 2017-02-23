import ckan.controllers.storage as storage
import os


import ckan.lib.uploader as uploader

from ckan.lib.base import request, h
from logging import getLogger

log = getLogger(__name__)

BASE_PATH = uploader.get_storage_path() +'/storage/'


def generate_response(http_status, unicode_body, error=False, no_cache=True, other_headers=None):
    r = request.environ['pylons.pylons'].response
    if no_cache:
        r.headers['Pragma'] = 'no-cache'
        r.headers['Cache-Control'] = 'max-age=0, no-store, no-cache'

    if other_headers:
        for key, value in other_headers.iteritems():
            r.headers[key] = value

    if unicode_body:
        r.body = unicode_body
    else:
        r.unicode_body = error
    r.status = http_status
    return r


class ImageController(storage.StorageController):
    def _download_file(self, relative_path, label):
        file_path = BASE_PATH + relative_path + label
        exists = os.path.isfile(file_path)
        if not exists:
            # handle erroneous trailing slash by redirecting to url w/o slash
            if label.endswith('/'):
                label = label[:-1]
                # This may be best being cached_url until we have moved it into
                # permanent storage
                file_url = h.url_for('storage_file', label=label)
                h.redirect_to(file_url)
            else:
                #                 abort(404)
                r = generate_response(404, None, error=u'File not found')
                return r

        with open(file_path, 'rb') as f:
            image = f.read()
        return generate_response(200, image, other_headers={'Content-type':'image'})


    def org_file(self, label):
        return self._download_file('uploads/group/', label)

    def dataset_file(self, label):
        return self._download_file('uploads/dataset/', label)

