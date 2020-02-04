import ckan.plugins.toolkit as tk


config = tk.config


def is_s3filestore_enabled():
    enabled = config.get('hdx.s3filestore')
    if enabled is None:
        enabled = 's3filestore' in config.get('ckan.plugins', '')
        config['hdx.s3filestore'] = enabled
    return enabled
