#
# ckan - Pylons testing environment configuration
#

[server:main]
use = egg:Paste#http
host = 0.0.0.0
port = 5000

[app:main]
use = egg:ckan
full_stack = true
cache_dir = %(here)s/data
debug = false

#faster_db_test_hacks = True

sqlalchemy.url = postgresql://ckan:ckan@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/ckan

## Datastore
ckan.datastore.write_url = postgresql://ckan:ckan@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/datastore
ckan.datastore.read_url = postgresql://datastore:datastore@${HDX_CKANDB_ADDR}:${HDX_CKANDB_PORT}/datastore

ckan.datapusher.url = http://datapusher.ckan.org/

## Solr support
solr_url = http://${HDX_SOLR_ADDR}:${HDX_SOLR_PORT}/solr/ckan

ckan.auth.user_create_organizations = false
ckan.auth.user_create_groups = false
ckan.auth.create_user_via_api = false
ckan.auth.create_user_via_web = true
ckan.auth.create_dataset_if_not_in_organization = true
ckan.auth.anon_create_dataset = false
ckan.auth.user_delete_groups=false
ckan.auth.user_delete_organizations=false
ckan.auth.create_unowned_dataset=true

# It's difficult to work with the user_show() action in tests if this is set to false
# so we only set it on tests where we need to test that this works with
# @pytest.mark.ckan_config(u"ckan.auth.public_user_details", False)
# ckan.auth.public_user_details=false

ckan.cache_validation_enabled = True
ckan.cache_enabled = False
ckan.tests.functional.test_cache.expires = 1800
ckan.tests.functional.test_cache.TestCacheBasics.test_get_cache_expires.expires = 3600

ckan.site_id = test.ckan.net
ckan.site_title = CKAN
ckan.site_logo = /images/ckan_logo_fullname_long.png
ckan.site_description =
package_form = standard
licenses_group_url =
# pyamqplib or queue
carrot_messaging_library = queue
ckan.site_url = http://test.ckan.net
#ckan.site_url = http://${HDX_DOMAIN}
package_new_return_url = http://localhost/dataset/<NAME>?test=new
package_edit_return_url = http://localhost/dataset/<NAME>?test=edit
ckan.resource_formats = %(here)s/ckanext-hdx_package/ckanext/hdx_package/config/resource_formats.json
ckan.extra_resource_fields = broken_link in_quarantine daterange_for_data pii_is_sensitive p_coded
ckan.resource_formats.external_system = External System

# Add additional test specific configuration options as necessary.
auth.blacklist = 83.222.23.234

search_backend = sql

# Change API key HTTP header to something non-standard.
apikey_header_name = X-Non-Standard-CKAN-API-Key

# only for 2.3
#ckan.plugins = stats
# only for 2.6
ckan.plugins = dcat dcat_json_interface structured_data hdx_dataviz expire_api_token hdx_hxl_preview ytp_request hdx_pages hdx_choropleth_map_view hdx_geopreview_view hdx_chart_views hdx_service_checker hdx_analytics hdx_search sitemap hdx_org_group hdx_group hdx_package hdx_user_extra hdx_mail_validate hdx_users hdx_theme security requestdata showcase resource_proxy text_view recline_view datastore activity
# ckan.plugins = ${HDX_ENABLED_PLUGINS}
ckan.views.default_views = recline_view
ckan.csrf_protection.ignore_extensions = false

ckan.use_pylons_response_cleanup_middleware = False

hdx.file_structure.check_url = http://${HDX_ANALYTICS_API}/api/file-structure-check/dataset/{dataset_id}/resource/{resource_id}
hdx.hxlproxy.url = https://proxy.hxlstandard.org
hdx.hxlproxy.source_info_url = ${HDX_HXLPROXY}/api/source-info?url={url}

hdx.onboarding.send_confirmation_email = true

# use <strong> so we can check that html is *not* escaped
ckan.template_head_end = <link rel="stylesheet" href="TEST_TEMPLATE_HEAD_END.css" type="text/css">

# use <strong> so we can check that html is *not* escaped
ckan.template_footer_end = <strong>TEST TEMPLATE_FOOTER_END TEST</strong>

# mailer
smtp.test_server = localhost:6675
smtp.mail_from = hdx@humdata.org

ckan.locale_default = en_AU
ckan.locale_order = en pt_BR ja it cs_CZ ca es fr el sv sr sr@latin no sk fi ru de pl nl bg ko_KR hu sa sl lv
ckan.locales_filtered_out =
ckan.datastore.enabled = 1

ckanext.stats.cache_enabled = 0

ckan.datasets_per_page = 20

ckan.activity_streams_email_notifications = True

ckan.activity_list_limit = 15

ckan.tracking_enabled = true

beaker.session.key = ckan
beaker.session.validate_key = ckan
beaker.session.secret = This_is_a_secret_or_is_it
# repoze.who config
who.config_file = %(here)s/ckan/config/who.ini
who.log_level = warning
who.log_file = %(cache_dir)s/who_log.ini

hdx.orgrequest.email = hdx@un.org
hdx.cache.onstartup = false

ckan.storage_path = /srv/filestore

# DATA GRID / COMPLETENESS
hdx.datagrid.config_url_pattern = https://raw.githubusercontent.com/OCHA-DAP/data-grid-recipes/{branch}/data%%20grid%%20recipe%%20-%%20{iso}.yml

# hdx.caching.dogpile_filename = /tmp/hdx_dogpile_cache.dbm

# HDX http headers
hdx.http_headers.routes = /country/topline/,/view/,/eaa-worldmap
hdx.http_headers.mimetypes = application/json,text/html,text/json

# Disabling email sending in tests
hdx.api_token.email_notifications.enabled = false

# FAQ - Wordpress
hdx.wordpress.url=https://centre.humdata.org
hdx.wordpress.category.faq=554
hdx.wordpress.category.devs=568
hdx.wordpress.category.terms=577
hdx.wordpress.category.licenses=581


# Logging configuration
[loggers]
keys = root, ckan, sqlalchemy

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_ckan]
qualname = ckan
handlers =
level = WARN

[logger_sqlalchemy]
handlers =
qualname = sqlalchemy.engine
level = WARN

[handler_console]
class = StreamHandler
args = (sys.stdout,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(asctime)s %(levelname)-5.5s [%(name)s] %(message)s


