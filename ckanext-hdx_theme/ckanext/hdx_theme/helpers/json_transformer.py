import json


def get_obj_from_json_in_dict(data_dict, json_property):
    try:
        result = json.loads(data_dict.get(json_property))
    except TypeError as e:
        result = {}
    return result
