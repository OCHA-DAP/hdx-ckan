# encoding: utf-8
import logging

from flask import Blueprint
from flask.views import MethodView
from paste.deploy.converters import asbool
from six import text_type

import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.lib.captcha as captcha
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.logic.schema as schema
import ckan.model as model
import ckan.plugins as plugins
from ckan import authz
from ckan.common import _, config, g, request
from ckan.views.user import EditView as EditView

log = logging.getLogger(__name__)

user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')


class HDXEditView(EditView):
    def get(self, id=None, data=None, errors=None, error_summary=None):
        if data is None:
            context, id = self._prepare(id)
            data_dict = {u'id': id}
            try:
                data = logic.get_action(u'user_show')(context, data_dict)
            except logic.NotAuthorized:
                base.abort(403, _(u'Unauthorized to edit user %s') % u'')
            except logic.NotFound:
                base.abort(404, _(u'User not found'))
        data['dan'] = 'Dan'
        return super(HDXEditView, self).get(id, data, errors, error_summary)


_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)
