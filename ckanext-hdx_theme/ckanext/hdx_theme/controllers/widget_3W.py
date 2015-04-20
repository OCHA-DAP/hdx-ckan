import ckan.lib.base as base
from ckan.common import request, response, json
import widget
import urlparse


render = base.render

class Widget3WController(widget.WidgetController):
    def _process(self, data):
        return data
    def _get_data(self):
        ret = {
            "geotype": "filestore",
            "description": "One Description Test for custom demo org",
            "joinAttribute": "DIST_NO",
            "colors": ["#ffb5ff", "#e09ee7", "#a371b8", "#855ba0", "#664488", "#472d71", "#291759", "#0a0041"],
            "whoFieldName": "Organisation",
            "whatFieldName": "Activity",
            "whereFieldName": "DIST_NO",
            "title": "One Test for custom demo org",
            "datatype": "filestore",
            "geo": "/dataset/custom-test-org-data/resource_download/2119ce9f-523b-46e3-b6ac-3d842db62d44",
            "zoom": "1500",
            "data": "/dataset/custom-test-org-data/resource_download/8e312caf-6755-4875-9b37-ebed76da90a5",
            "y": "6",
            "x": "46",
            "type": ""
        }
        keys = ["geotype", "description", "joinAttribute", "colors", "whoFieldName", "whatFieldName", "whereFieldName", "title", "datatype", "geo", "zoom", "data", "y", "x"];


        config = urlparse.parse_qs(request.url.split("?")[1])
        ret.update(config)

        return ret
    def show(self):
        raw_data = self._get_data()
        data = self._process(raw_data)

        result = render('widget/3W/3W.html', extra_vars={"data": json.dumps(data)})
        return result
