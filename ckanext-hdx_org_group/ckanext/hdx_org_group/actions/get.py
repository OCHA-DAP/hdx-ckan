'''
Created on April 24, 2015

@author: alexandru-m-g
'''
from ckan import logic as logic, model
from ckan.lib import dictization as d
from ckanext.hdx_org_group.helpers.organization_helper import _get_or_bust, NotFound

@logic.side_effect_free
def hdx_topline_num_for_group(context, data_dict):



@logic.side_effect_free
def hdx_light_group_show(context, data_dict):
    id = _get_or_bust(data_dict, "id")
    group_dict = {}
    group = model.Group.get(id)
    if not group:
        raise NotFound
    #group_dict['group'] = group
    group_dict['id'] = group.id
    group_dict['name'] = group.name
    group_dict['image_url'] = group.image_url
    group_dict['display_name'] = group_dict['title'] = group.title
    group_dict['description'] = group.description
    group_dict['revision_id'] = group.revision_id

    result_list = []
    for name, extra in group._extras.iteritems():
        dictized = d.table_dictize(extra, context)
        if not extra.state == 'active':
            continue
        value = dictized["value"]
        result_list.append(dictized)

        #Keeping the above for backwards compatibility
        group_dict[name]= dictized["value"]

    group_dict['extras'] = sorted(result_list, key=lambda x: x["key"])
    return group_dict