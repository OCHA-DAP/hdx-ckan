import flask
import logging
import mimetypes

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.uploader import GlobalUpload, get_base_path

abort = tk.abort
_ = tk._

log = logging.getLogger(__name__)

hdx_global_file_server = flask.Blueprint(u'hdx_global_file_server', __name__, url_prefix=u'/global')
hdx_local_image_server = flask.Blueprint(u'hdx_local_image_server', __name__, url_prefix=u'/image')


def global_file_download(filename):
    upload = GlobalUpload({
        'filename': filename,
        'upload': None
    })
    filepath = upload.get_path()
    return _download_file(filepath, filename)


def _download_file(filepath, filename):
    try:
        resp = flask.send_file(filepath)
        content_type, content_enc = mimetypes.guess_type(filename)
        if content_type:
            resp.headers[u'Content-Type'] = content_type
        return resp
    except (OSError, IOError):
        abort(404, _('Resource data not found'))


def org_file(filename):
    base_path = get_base_path() + '/storage/'
    file_path = base_path + 'uploads/group/' + filename
    return _download_file(file_path, filename)


hdx_global_file_server.add_url_rule(u'/<filename>', view_func=global_file_download)
hdx_local_image_server.add_url_rule(u'/<filename>', view_func=org_file)
