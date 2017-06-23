[DEFAULT]
debug = false

[server:main]
use = egg:Paste#http
host = 0.0.0.0
port = 9221

[app:main]
use = egg:ckan
use = config:/srv/ckan/common-config-ini.txt
## Database Settings
sqlalchemy.url           = postgresql://ckan:ckan@dbckan:5432/ckan
ckan.datastore.write_url = postgresql://ckan:ckan@dbckan:5432/datastore
ckan.datastore.read_url  = postgresql://datastore:datastore@dbckan:5432/datastore
#sqlalchemy.url = postgresql://ckan:ckan@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/ckan
#ckan.datastore.write_url = postgresql://ckan:ckan@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/datastore
#ckan.datastore.read_url = postgresql://datastore:datastore@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/datastore

## Site Settings
ckan.site_url = http://${HDX_PREFIX}data.${HDX_DOMAIN}
beaker.session.secret = 2yD+TJxTgW+VtA38OzxQJNPPO
app_instance_uuid = {0bcda427-a808-470f-a141-37eb1ac46ba1}

## Search Settings
ckan.site_id = default
solr_url = http://solr:8983/solr/ckan
#solr_url = http://${HDX_SOLR_ADDR}:${HDX_SOLR_PORT}/solr/ckan
#ckan.simple_search = 1

ckan.recaptcha.publickey  = 6LfoIfMSAAAAADKSmGKOsRggVKv4CAOm2yqJoeto
ckan.recaptcha.privatekey = ${HDX_CKAN_RECAPTCHA_KEY}

ckan.tracking_enabled = true

## Email settings

email_to         = ckan.${HDX_TYPE}@${HDX_DOMAIN}
error_email_from = ckan.${HDX_TYPE}@${HDX_DOMAIN}
smtp_server      = email:25
smtp.server      = email:25
#smtp_server = ${HDX_SMTP_ADDR}:${HDX_SMTP_PORT}
#smtp.server = ${HDX_SMTP_ADDR}:${HDX_SMTP_PORT}
smtp.starttls    = False
smtp.mail_from   = noreply@${HDX_DOMAIN}

hdx.cache.onstartup = true

hdx.orgrequest.email = hdx.feedback@gmail.com
hdx.orgrequest.sendmails = true

hdx.datapreview.url = /dataproxy
#hdx.ogre.url = /ogre
#hdx.previewmap.url = /tiles/{z}/{x}/{y}.png
hdx.previewmap.url = /crisis-tiles/{z}/{x}/{y}.png
hdx.crisismap.url  = /crisis-tiles/{z}/{x}/{y}.png
#https://{s}.tiles.mapbox.com/v3/reliefweb.l43d4f5j/{z}/{x}/{y}.png
hdx.mapbox.baselayer.url   = /mapbox-base-tiles/{z}/{x}/{y}.png
#https://{s}.tiles.mapbox.com/v3/reliefweb.l43djggg/{z}/{x}/{y}.png
hdx.mapbox.labelslayer.url = /mapbox-layer-tiles/{z}/{x}/{y}.png

hdx.rest.indicator.endpoint        = http://${HDX_PREFIX}manage.${HDX_DOMAIN}/public/api2/values
hdx.rest.indicator.endpoint.facets = http://${HDX_PREFIX}manage.${HDX_DOMAIN}/public/api2

ckan.storage_path = ${HDX_FILESTORE}

hdx.css.basepath           = /srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/public/css/generated
hdx.less.basepath          = /srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/less
hdx.less_compile.onstartup = False

# GIS
hdx.gis.layer_import_url = http://gislayer:5000/api/add-layer/dataset/{dataset_id}/resource/{resource_id}?resource_download_url={resource_download_url}&url_type={url_type}
#hdx.gis.layer_import_url = http://${HDX_GISLAYER_ADDR}:${HDX_GISLAYER_PORT}/api/add-layer/dataset/{dataset_id}/resource/{resource_id}?resource_download_url={resource_download_url}&url_type={url_type}
# this is only needed for the clients to get the pbf
# at Alex suggestion, i made this proto unaware
hdx.gis.resource_pbf_url = //${HDX_PREFIX}data.${HDX_DOMAIN}/gis/services/postgis/{resource_id}/wkb_geometry/vector-tiles/{z}/{x}/{y}.pbf

hdx.analytics.mixpanel.token = ${HDX_MIXPANEL_TOKEN}
hdx.analytics.enqueue_url    = http://gislayer:5000/api/send-analytics
#hdx.analytics.enqueue_url    = http://${HDX_GISLAYER_ADDR}:${HDX_GISLAYER_PORT}/api/send-analytics

# HXL Proxy
# This should be overriden in your own prod.ini
hdx.hxlproxy.url = https://${HDX_PREFIX}data.${HDX_DOMAIN}/hxlproxy

# HXL Preview
hdx.hxl_preview_app.url = https://${HDX_PREFIX}data.${HDX_DOMAIN}/hxlpreview

# GOOGLE DEV
hdx.google.dev_key = ${HDX_GOOGLE_DEV_KEY}

# MAILCHIMP
hdx.mailchimp.api.key = ${HDX_MAILCHIMP_API_KEY}
hdx.mailchimp.list.newsletter = ${HDX_MAILCHIMP_LIST_NEWSLETTER}
hdx.mailchimp.list.newuser = ${HDX_MAILCHIMP_LIST_NEW_USER}

hdx.active_locations_reliefweb.resource_id = 4551480e-448e-4b09-b02f-ed31d42a43d5

## Logging configuration
[loggers]
keys = root, ckan, ckanext

[handlers]
keys = console, file

[formatters]
keys = generic

[logger_root]
level = WARNING
handlers = console, file

[logger_ckan]
level = WARNING
handlers = console, file
qualname = ckan
propagate = 0

[logger_ckanext]
level = WARNING
handlers = console, file
qualname = ckanext
propagate = 0

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[handler_file]
class = FileHandler
args = ('/var/log/ckan/ckan.pain.log','a')
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s
