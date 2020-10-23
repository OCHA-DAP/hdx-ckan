import itertools
import json
import os
from collections import OrderedDict

from pylons import config

import ckan

_ALLOWED_FORMATS = None # type dict


def guess_format_from_extension(extension):
    allowed_resource_formats = allowed_formats()
    return allowed_resource_formats.get(extension.lower())


def resource_format_autocomplete(query, limit):
    allowed_resource_formats = allowed_formats()

    result_generator = (value for key, value in allowed_resource_formats.items() if query.lower() in key)
    result_generator = itertools.islice(result_generator, 7)
    result = list(result_generator)
    result.sort()
    return result


def allowed_formats():
    global _ALLOWED_FORMATS
    if not _ALLOWED_FORMATS:
        format_file_path = config.get('ckan.resource_formats')
        if not format_file_path:
            format_file_path = os.path.join(
                os.path.dirname(os.path.realpath(ckan.config.__file__)),
                'resource_formats.json'
            )
        with open(format_file_path) as format_file:
            try:
                file_resource_formats = json.loads(format_file.read())
            except ValueError as e:
                # includes simplejson.decoder.JSONDecodeError
                raise ValueError('Invalid JSON syntax in %s: %s' %
                                 (format_file_path, e))

            temp_list = []
            for format_line in file_resource_formats:
                if format_line[0] == '_comment':
                    continue
                temp_list.append((format_line[0].lower(), format_line[0]))
                temp_list.append((format_line[1].lower(), format_line[0]))
                for alternative_format in format_line[3]:
                    temp_list.append((alternative_format, format_line[0]))

            temp_list.sort(key=lambda item: item[1])
            # _ALLOWED_FORMATS = {tpl[0]: tpl[1] for tpl in temp_list}
            _ALLOWED_FORMATS = OrderedDict(temp_list)

    return _ALLOWED_FORMATS
