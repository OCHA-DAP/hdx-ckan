import requests

import ckan.plugins.toolkit as tk

config = tk.config


def do_hxl_transformation(source_url, transformer):
    '''
    :param source_url:
    :type source_url: str
    :param transformer:
    :type transformer: ckanext.hdx_theme.hxl.transformers.transformers.BasicTransformer
    :return: json response from hxl proxy
    '''
    proxy_url = config.get('hdx.hxlproxy.url') + '/data.json'
    params = {
        'url': source_url,
        'recipe': transformer.generateJsonFromRecipes()
    }

    response = requests.get(proxy_url, params=params, verify=False)

    response.raise_for_status()

    return response.json()


def transform_response_to_dict_list(json_response, custom_mapping=None):
    ret_list = []
    custom_mapping = custom_mapping if custom_mapping else {}
    if json_response and len(json_response) >= 3:

        for line in json_response[2:]:
            line_dict = {
                custom_mapping.get(json_response[1][i], json_response[1][i]):value for i,value in enumerate(line)
            }
            ret_list.append(line_dict)

    return ret_list

