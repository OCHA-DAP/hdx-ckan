import six
from ckanext.hdx_package.helpers.resource_triggers.geopreview import get_action, log, _before_ckan_action, \
    _after_ckan_action
from ckanext.hdx_theme.helpers.hash_generator import generate_hash_dict, HashCodeGenerator


def trigger_4_resource_changes(before_resource_change_actions, after_resource_change_actions):

    def package_action_wrapper(original_package_action):

        def package_action(context, package_dict):

            # package_update() can be done with: context['allow_partial_update'] = True - which allows skipping
            # the resource list from the dataset_dict. In this case geopreview should be skipped.
            new_resources = package_dict.get('resources', [])

            resource_id_to_modified_map = {}
            if new_resources:
                old_package_dict = get_action('package_show')(context, {'id': package_dict.get('id')}) \
                    if 'id' in package_dict else {}

                old_resources_list = old_package_dict.get('resources')
                fields = ['name', 'description', 'url', 'format']

                resource_id_to_hash_map = {}

                if old_resources_list:
                    try:
                        # We compute a hash code for "old" resource to see if they have changed
                        resource_id_to_hash_map = generate_hash_dict(old_resources_list, 'id', fields)
                    except Exception as e:
                        log.error(six.text_type(e))

                for resource_dict in new_resources:
                    modified_or_new = True
                    try:
                        if 'id' in resource_dict and not 'upload' in resource_dict:
                            rid = resource_dict['id']
                            hash_code = HashCodeGenerator(resource_dict, fields).compute_hash()
                            modified_or_new = False if resource_id_to_hash_map.get(rid) == hash_code else True
                            resource_id_to_modified_map[rid] = modified_or_new
                    except Exception as e:
                        log.error(six.text_type(e))

                    if modified_or_new:
                        for before_action in before_resource_change_actions:
                            before_action(context, resource_dict)

            result_dict = original_package_action(context, package_dict)

            # If it comes from resource_create / resource_update the transaction is not yet committed
            # (resource is not yet saved )
            if isinstance(result_dict, dict):
                if new_resources and not context.get('defer_commit', False):
                    for resource_dict in result_dict.get('resources', []):

                        # default is True, because new resources wouldn't be in the map at all
                        if resource_id_to_modified_map.get(resource_dict['id'], True):
                            for after_action in after_resource_change_actions:
                                after_action(context, resource_dict)
            else:
                log.info("result_dict variable is not a dict but: {}".format(str(result_dict)))

            return result_dict

        return package_action

    return package_action_wrapper
