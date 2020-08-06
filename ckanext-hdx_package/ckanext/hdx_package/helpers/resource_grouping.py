from ckanext.hdx_package.helpers.constants import COD_VALUES_MAP
from ckanext.hdx_package.helpers.date_helper import DaterangeParser


OTHER_MENU_LABEL = 'Unspecified'


def set_show_groupings_flag(dataset_dict):
    cod_level = dataset_dict.get('cod_level')
    if cod_level:
        dataset_dict['x_show_grouping'] = COD_VALUES_MAP.get(cod_level).get('is_cod') \
                                          and dataset_dict.get('x_resource_grouping')


def add_other_grouping_if_needed(dataset_dict):
    dataset_groupings = set(dataset_dict.get('x_resource_grouping'))
    other_added = False
    for r in dataset_dict.get('resources', []):
        if r.get('grouping') not in dataset_groupings:
            r['x_grouping'] = OTHER_MENU_LABEL
            if not other_added:
                other_added = True
                dataset_dict['x_resource_grouping'].append(OTHER_MENU_LABEL)

        else:
            r['x_grouping'] = r.get('grouping')


class ResourceGrouping(object):

    def __init__(self, dataset_dict):
        self.dataset_dict = dataset_dict
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

    def _get_sorted_groupings(self):
        result = [
            item[0] for item in
            sorted(self.groupings_dict.items(), key=lambda x: x[1], reverse=True)
        ]
        return result

    def populate_computed_groupings(self):
        saved_grouping = self.dataset_dict.get('resource_grouping')
        computed_grouping = saved_grouping if saved_grouping else self._get_sorted_groupings()
        self.dataset_dict['x_resource_grouping'] = computed_grouping
        return self

