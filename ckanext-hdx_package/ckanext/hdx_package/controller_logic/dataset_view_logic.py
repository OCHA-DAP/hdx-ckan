import ckan.plugins.toolkit as tk

from ckanext.hdx_package.helpers.resource_triggers.geopreview import GIS_FORMATS, get_latest_shape_info

config = tk.config


def process_shapes(resources, id=None):
    result = []

    for resource in resources:
        if has_shape_info(resource):
            res_pbf_template_url = config.get('hdx.gis.resource_pbf_url')
            shp_info = get_latest_shape_info(resource)

            res_pbf_url = res_pbf_template_url.replace('{resource_id}', shp_info['layer_id'])
            name = resource['name']
            shp_dict = {
                'resource_name': name,
                'url': res_pbf_url,
                'bounding_box': shp_info['bounding_box'],
                'layer_fields': shp_info.get('layer_fields', []),
                'layer_id': shp_info['layer_id'],
            }
            if resource.get('id') == id:
                result.insert(0, shp_dict)
            else:
                result.append(shp_dict)
    return result


def has_shape_info(resource):
    if resource.get('format', '').lower() in GIS_FORMATS and resource.get('shape_info'):
        shp_info = get_latest_shape_info(resource)
        if shp_info.get('state', '') == 'success':
            return {'type': 'hdx_geo_preview', 'default': None}
    return None
