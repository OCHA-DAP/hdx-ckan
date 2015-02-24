import urllib

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.lib.dictization as dictization

from ckan.common import _, c


abort = base.abort
render = base.render
_get_action = logic.get_action


class PcodeController(base.BaseController):

    def pcode_mapper(self, id, resource_id, data=None, errors=None,
                      error_summary=None):
        return self._pcode_mapper(id, resource_id)

    def _pcode_mapper(self, id, resource_id, data=None, errors=None,
                      error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {}

        template_data = {
            'data': {
                'resouce_id': resource_id,
                'dataset_id': id
            },
            'errors': errors,
            'error_summary': error_summary,
        }

        result = render(
            'package/custom/pcode_mapper.html', extra_vars=template_data)

        return result

