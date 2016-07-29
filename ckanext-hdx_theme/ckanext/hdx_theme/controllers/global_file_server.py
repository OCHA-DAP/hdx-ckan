import mimetypes

import paste.fileapp as fileapp

import ckan.lib.base as base

from ckan.common import _, request, response

from ckanext.hdx_theme.helpers.uploader import GlobalUpload


class GlobalFileController(base.BaseController):

    def global_file_download(self, filename):
        upload = GlobalUpload({
            'filename': filename,
            'upload': None
        })
        filepath = upload.get_path()
        fapp = fileapp.FileApp(filepath)
        try:
            status, headers, app_iter = request.call_application(fapp)
            response.headers.update(dict(headers))
            content_type, content_enc = mimetypes.guess_type(filename)
            if content_type:
                response.headers['Content-Type'] = content_type
            response.status = status
            return app_iter
        except OSError:
            base.abort(404, _('Resource data not found'))