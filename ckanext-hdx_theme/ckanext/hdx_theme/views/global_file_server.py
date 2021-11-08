import flask
import logging
import mimetypes

import ckan.plugins.toolkit as tk


abort = tk.abort
_ = tk._

log = logging.getLogger(__name__)

hdx_global_file_server = flask.Blueprint(u'hdx_global_file_server', __name__, url_prefix=u'/global')

from ckanext.hdx_theme.helpers.uploader import GlobalUpload


def global_file_download(filename):
    upload = GlobalUpload({
        'filename': filename,
        'upload': None
    })
    try:
        filepath = upload.get_path()
        resp = flask.send_file(filepath)
        content_type, content_enc = mimetypes.guess_type(filename)
        if content_type:
            resp.headers[u'Content-Type'] = content_type
        return resp
    except (OSError, IOError):
        abort(404, _('Resource data not found'))


hdx_global_file_server.add_url_rule(u'/<filename>', view_func=global_file_download)
