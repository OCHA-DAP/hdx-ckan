# -*- coding: utf-8 -*-

import os
from ckan.config.middleware import make_app
from ckan.cli import CKANConfigLoader
from logging.config import fileConfig as loggingFileConfig

if os.environ.get(u'CKAN_INI'):
    config_path = os.environ[u'CKAN_INI']
else:
    config_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), u'ckan.ini')

if not os.path.exists(config_path):
    raise RuntimeError(u'CKAN config option not found: {}'.format(config_path))

loggingFileConfig(config_path)
config = CKANConfigLoader(config_path).get_config()

application = make_app(config)

from elasticapm.contrib.flask import ElasticAPM

apm = ElasticAPM(app=application._wsgi_app,
    service_name=os.getenv('ELASTIC_APM_SERVICE_NAME'),
    server_url=os.getenv('ELASTIC_APM_SERVER_URL'),
    secret_token=os.getenv('ELASTIC_APM_SECRET_TOKEN'),
    environment=os.getenv('ELASTIC_APM_ENVIRONMENT'),
    enabled=os.getenv('ELASTIC_APM_ENABLED')
)
