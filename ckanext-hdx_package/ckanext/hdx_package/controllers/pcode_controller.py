import urllib

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
get_action = logic.get_action
import requests
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.lib.dictization as dictization

from ckan.common import _, c


abort = base.abort
render = base.render


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

        data_dict['xml_url'] = 'http://gistmaps.itos.uga.edu/arcgis/services/COD_External/MLI_pcode/MapServer/WFSServer?request=GetFeature&service=WFS&typeNames=COD_External_MLI_pcode:Admin2&maxFeatures=99999'
        data_dict['convert_url'] = u'http://ogre.adc4gis.com/convert'
        result1 = get_action('hdx_get_pcode_mapper_values')({}, data_dict)
        print result1
        result = render('package/custom/pcode_mapper.html', extra_vars=template_data)

        return result

