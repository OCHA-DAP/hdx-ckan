import logging

import ckan.lib.uploader as uploader
import ckan.plugins.toolkit as toolkit


log = logging.getLogger(__name__)
chained_action = toolkit.chained_action
_check_access = toolkit.check_access


@chained_action
def chained_showcase_update(original_action, context, data_dict):
    return _showcase_update(context, data_dict)


def _showcase_update(context, data_dict):

    _check_access('ckanext_showcase_update', context, data_dict)
    # If get_uploader is available (introduced for IUploader in CKAN 2.5), use
    # it, otherwise use the default uploader.
    # https://github.com/ckan/ckan/pull/2510
    try:
        upload = uploader.get_uploader('showcase', data_dict['image_url'])
    except AttributeError:
        upload = uploader.Upload('showcase', data_dict['image_url'])

    if 'image_upload' in data_dict:
        # mimetype is needed before uploading to AWS S3
        upload.mimetype = getattr(data_dict['image_upload'], 'type', 'application/octet-stream')
    upload.update_data_dict(data_dict, 'image_url',
                            'image_upload', 'clear_upload')

    upload.upload(uploader.get_max_image_size())

    pkg = toolkit.get_action('package_update')(context, data_dict)

    return pkg
