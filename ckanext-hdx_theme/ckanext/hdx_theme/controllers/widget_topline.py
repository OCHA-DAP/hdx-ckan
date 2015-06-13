import ckan.lib.base as base

import widget

render = base.render

class WidgetToplineController(widget.WidgetController):
    def _process(self, data):
        return data
    def _get_data(self):
        return {
            "title": "Cumulative Cases of Ebola",
            "formatted_value": "20,747",
            "units": "$",
            "notes": "These are cumulative cases of Ebola",
            "sparklines_json": "",
            "source": "WHO",
            "source_link": "https://data.hdx.rwlabs.org/dataset/ebola-cases-2014",
            "explore": "http://docs.hdx.rwlabs.org/west-africa-ebola-outbreak-visualization/",
            "latest_date": "Jan 07, 2015"
        }
    def show(self):
        raw_data = self._get_data()
        data = self._process(raw_data)

        result = render('widget/topline/topline.html', extra_vars=data)
        return result
