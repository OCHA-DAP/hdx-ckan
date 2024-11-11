[DEFAULT]
debug = false
smtp_server      = ${HDX_SMTP_ADDR}:${HDX_SMTP_PORT}
smtp_username    = ${HDX_SMTP_USER}
smtp_password    = ${HDX_SMTP_PASS}
smtp_use_tls     = ${HDX_SMTP_TLS}

[server:main]
use = egg:Paste#http
host = 0.0.0.0
port = 5000

[app:main]
use = config:/srv/ckan/common-config-ini.txt
## Database Settings
sqlalchemy.url = postgresql://${HDX_CKANDB_USER}:${HDX_CKANDB_PASS}@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/${HDX_CKANDB_DB}
ckan.datastore.write_url = postgresql://${HDX_CKANDB_USER}:${HDX_CKANDB_PASS}@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/${HDX_CKANDB_DB_DATASTORE}
ckan.datastore.read_url = postgresql://${HDX_CKANDB_USER_DATASTORE}:${HDX_CKANDB_PASS_DATASTORE}@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/${HDX_CKANDB_DB_DATASTORE}

## Site Settings
ckan.site_url = https://${HDX_DOMAIN}
beaker.session.secret = ${BEAKER_SECRET}
beaker.session.cookie_domain = ${HDX_DOMAIN}
beaker.session.url = redis://${HDX_SESSION_REDIS_ADDR}:${HDX_SESSION_REDIS_PORT}/${HDX_SESSION_REDIS_DB}
app_instance_uuid = {0bcda427-a808-470f-a141-37eb1ac46ba1}

## Search Settings
ckan.site_id = default
#solr_url = http://solr:8983/solr/ckan
solr_url = http://${HDX_SOLR_ADDR}:${HDX_SOLR_PORT}/solr/${HDX_SOLR_CORE}
#ckan.simple_search = 1

ckan.recaptcha.publickey  = 6Lcl60EUAAAAAE46a3XcPM2nPUKI2K4XZbcsorkR
ckan.recaptcha.privatekey = ${HDX_CKAN_RECAPTCHA_KEY}

ckan.tracking_enabled = true

# WEBASSETS
ckan.webassets.path = ${HDX_WEBASSETS_PATH}

## Email settings

email_to         = ckan@${HDX_SMTP_DOMAIN}
error_email_from = ckan@${HDX_SMTP_DOMAIN}
smtp.mail_from   = hdx@${HDX_SMTP_DOMAIN}
smtp.server      = ${HDX_SMTP_ADDR}:${HDX_SMTP_PORT}
smtp.user        = ${HDX_SMTP_USER}
smtp.password    = ${HDX_SMTP_PASS}
smtp.starttls    = ${HDX_SMTP_TLS}

## DOWNLOAD WITH CACHE DATASETS
# accepting comma separated list with no spaces
hdx.download_with_cache.datasets = repository-for-pdf-files
hdx.download_with_cache.folder = /srv/filestore/download_cache

hdx.cache.onstartup = true
hdx.caching.redis_host = ${HDX_REDIS_ADDR}
hdx.caching.redis_port = ${HDX_REDIS_PORT}
hdx.caching.redis_db = ${HDX_REDIS_DB}

hdx.orgrequest.email = hdx@un.org
hdx.orgrequest.sendmails = true

# GIS
hdx.gis.layer_delete_url = http://${HDX_GEOPREVIEW_API}/api/delete-one-layer/{resource_id}
hdx.gis.layer_import_url = http://${HDX_GEOPREVIEW_API}/api/add-layer/dataset/{dataset_id}/resource/{resource_id}?resource_download_url={resource_download_url}&url_type={url_type}
#hdx.gis.layer_import_url = http://${HDX_GISLAYER_ADDR}:${HDX_GISLAYER_PORT}/api/add-layer/dataset/{dataset_id}/resource/{resource_id}?resource_download_url={resource_download_url}&url_type={url_type}
# this is only needed for the clients to get the pbf
# at Alex suggestion, i made this proto unaware
hdx.gis.resource_pbf_url = //${HDX_DOMAIN}/gis/{resource_id}/{z}/{x}/{y}.pbf

hdx.analytics.mixpanel.token = ${HDX_MIXPANEL_TOKEN}
hdx.analytics.mixpanel.secret = ${HDX_MIXPANEL_SECRET}
hdx.analytics.enqueue_url    = http://${HDX_ANALYTICS_API}/api/send-analytics
#hdx.analytics.enqueue_url    = http://${HDX_GISLAYER_ADDR}:${HDX_GISLAYER_PORT}/api/send-analytics
hdx.analytics.hours_for_results_in_cache = ${HDX_HOURS_MIXPANEL_CACHE}
#API Tracking
hdx.analytics.track_api = ${HDX_ANALYTICS_TRACK_API}
hdx.analytics.track_api.exclude_browsers = ${HDX_ANALYTICS_TRACK_API_EXCLUDE_BROWSERS}
hdx.analytics.track_api.exclude_other = ${HDX_ANALYTICS_TRACK_API_EXCLUDE_OTHER}

#file structure check
hdx.file_structure.check_url = http://${HDX_ANALYTICS_API}/api/file-structure-check/dataset/{dataset_id}/resource/{resource_id}

# HXL Proxy
# This should be overriden in your own prod.ini
hdx.hxlproxy.url = ${HDX_HXLPROXY}
hdx.hxlproxy.source_info_url = ${HDX_HXLPROXY}/api/source-info?url={url}

# Quickcharts!
hdx.hxl_preview_app.url = https://${HDX_DOMAIN}/tools/quickcharts

# MAILCHIMP
hdx.mailchimp.api.key = ${HDX_MAILCHIMP_API_KEY}
hdx.mailchimp.interest.data_services = ${HDX_MAILCHIMP_INTEREST_DATA_SERVICES}
hdx.mailchimp.list.newsletter = ${HDX_MAILCHIMP_LIST_NEWSLETTER}
hdx.mailchimp.list.newuser = ${HDX_MAILCHIMP_LIST_NEW_USER}

hdx.active_locations_reliefweb.resource_id = 4551480e-448e-4b09-b02f-ed31d42a43d5

# Dataset Validation
hdx.validation.allow_skip_for_sysadmin = dataset_date,notes,maintainer,methodology,methodology_other,data_update_frequency,groups_list,resources/format

# DATA GRID / COMPLETENESS
hdx.datagrid.config_url_pattern = https://raw.githubusercontent.com/OCHA-DAP/data-grid-recipes/{branch}/data%%20grid%%20recipe%%20-%%20{iso}.yml

# if true, caching will be enabled and the "master" branch from the github repo will be used
hdx.datagrid.prod = ${HDX_DATAGRID_PROD}

# QA dashboard
hdx.qadashboard.enabled = ${HDX_QA_DASHBOARD}

# P-CODE
hdx.p_code.new_filters.enabled = ${HDX_P_CODE_NEW_FILTERS_ENABLED}

# FAQ - Wordpress
hdx.wordpress.url = ${HDX_WORDPRESS_URL}
hdx.wordpress.auth.basic = ${HDX_WORDPRESS_AUTH_BASIC}

# HDX http headers
#hdx.http_headers.routes = /country/topline/,/view/,/eaa-worldmap
#hdx.http_headers.mimetypes = application/json,text/html,text/json

# add s3 config
ckanext.s3filestore.aws_access_key_id = ${AWS_ACCESS_KEY_ID}
ckanext.s3filestore.aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
ckanext.s3filestore.aws_bucket_name = ${AWS_BUCKET_NAME}
ckanext.s3filestore.host_name = https://s3.${REGION_NAME}.amazonaws.com
ckanext.s3filestore.region_name= ${REGION_NAME}
ckanext.s3filestore.signature_version = s3v4
ckanext.s3filestore.check_access_on_startup = true
ckan.storage_path = ${HDX_FILESTORE}

# jwt
api_token.jwt.decode.secret = string\:${HDX_JWT_SECRET}
api_token.jwt.encode.secret = string\:${HDX_JWT_SECRET}

# Security Extension Config
ckanext.security.domain = ${HDX_DOMAIN}
ckanext.security.redis.host = ${HDX_SECURITY_REDIS_ADDR}
ckanext.security.redis.port = ${HDX_SECURITY_REDIS_PORT}
ckanext.security.redis.db = ${HDX_SECURITY_REDIS_DB}
hdx.security.site_name = ${HDX_SECURITY_SITENAME}

# Change detection settings
hdx.change_detection.layer_url = http://${HDX_GEOPREVIEW_API}/api/create-change-events

# HDX Notification Platform
hdx.notifications.novu.api_key = ${HDX_NOVU_API_KEY}
hdx.notifications.enabled_datasets_csv = ${HDX_ENABLED_DATASETS_CSV}

## Logging configuration
[loggers]
keys = root, ckan, ckanext, ckanext.hdx_theme.util.timer

[handlers]
keys = console, file, jsonFile

[formatters]
keys = generic, jsonFormatter

[logger_root]
level = ${HDX_LOG_LEVEL}
handlers = console, file, jsonFile

[logger_ckan]
level = WARNING
handlers = console, file, jsonFile
qualname = ckan
propagate = 0

[logger_ckanext]
level = ${HDX_LOG_LEVEL}
handlers = console, file, jsonFile
qualname = ckanext
propagate = 0

[logger_ckanext.hdx_theme.util.timer]
level = INFO
handlers = console, file, jsonFile
qualname = ckanext.hdx_theme.util.timer
propagate = 0

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[handler_file]
class = FileHandler
args = ('/var/log/ckan/ckan.log','a')
level = NOTSET
formatter = generic

[handler_jsonFile]
class = FileHandler
args = ('/var/log/ckan/ckan.json.log','a')
level = NOTSET
formatter = jsonFormatter

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s

[formatter_jsonFormatter]
format = %(asctime)s %(levelname) %(threadName)s %(name)s %(lineno)d %(message)s %(funcName)s
class = pythonjsonlogger.jsonlogger.JsonFormatter
