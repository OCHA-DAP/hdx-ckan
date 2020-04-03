import ckan.plugins.toolkit as tk
get_action = tk.get_action


def hdx_get_page_list_for_dataset(context, dataset_dict):
    _page_list = []
    for tag in dataset_dict.get('tags'):
        _list = get_action('page_list_by_tag_id')(context, {'id': tag.get('id')})
        _page_list.extend(_list)
    result = {v['id']: v for v in _page_list}.values()
    return result
