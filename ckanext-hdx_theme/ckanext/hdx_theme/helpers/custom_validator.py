import ckan.lib.navl.dictization_functions as df

from ckan.common import _


def general_value_in_list(value_list, allow_not_selected, not_selected_value='-1'):

    def verify_value_in_list(key, data, errors, context):

        value = data.get(key)
        if allow_not_selected and value == not_selected_value:
            del data[key]
            # Don't go further in the validation chain. Ex: convert to extras doesn't need to be called
            raise df.StopOnError
        if not value or value not in value_list:
            raise df.Invalid(_('needs to be a value from the list'))

    return verify_value_in_list

