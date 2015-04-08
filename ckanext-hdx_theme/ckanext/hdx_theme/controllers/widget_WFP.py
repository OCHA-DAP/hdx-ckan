import ckan.lib.base as base
from ckan.common import request, response, json
import widget
import urlparse
from pylons import config
import ckanext.hdx_org_group.controllers.custom_org_controller as org_controller



render = base.render

class WidgetWFPController(widget.WidgetController):
    def _process(self, data):
        return data
    def _get_data(self):
        ret = {
            "type": "WFP",
            "embeded": True
        }
        keys = []

        # config = urlparse.parse_qs(request.url.split("?")[1])
        # for key in config:
        #     if isinstance(ret[key], list):
        #         ret[key] = config[key]
        #     else:
        #         ret[key] = config[key][0]

        return ret
    def show(self):
        raw_data = self._get_data()
        data = self._process(raw_data)

        extra = {
            "data": json.dumps(data),
            "visualization_basemap_url": config.get("hdx.orgmap.url"),
            "visualization_embed_url": org_controller._get_embed_url({'type': 'WFP', })
        }

        result = render('widget/WFP/WFP.html', extra_vars=extra)
        return result
