from ckanext.hdx_package.helpers.date_helper import DaterangeParser


class ResourceGrouping(object):
    def __init__(self, dataset_dict):
        self.groupings_dict = {}
        if dataset_dict and dataset_dict.get('resources'):
            for r in dataset_dict.get('resources'):
                self._populate_with_grouping_for_resource(r)

    def _populate_with_grouping_for_resource(self, r):
        if r.get('daterange_for_data') and r.get('grouping'):
            daterange_parser = DaterangeParser(r.get('daterange_for_data'))
            grouping = r.get('grouping')
            existing_start_date = self.groupings_dict.get(grouping)
            if not existing_start_date or daterange_parser.start_date > existing_start_date:
                self.groupings_dict[grouping] = daterange_parser.start_date

    def get_sorted_groupings(self):
        result = [
            item[0] for item in
            sorted(self.groupings_dict.items(), key=lambda x: x[1], reverse=True)
        ]
        return result

