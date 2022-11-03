#!/bin/sh

# disable qa_dashboard by default
export HDX_QA_DASHBOARD=${HDX_QA_DASHBOARD:-false}

# configure prod.ini
[ -f /etc/ckan/prod.ini ] || envsubst < /srv/ckan/docker/prod.ini.tpl > /etc/ckan/prod.ini

# and a copy of it to be used by less compile verbose mode
[ -f /etc/ckan/less.ini ] || cat /etc/ckan/prod.ini | sed 's/level = WARNING/level = INFO/' > /etc/ckan/less.ini;
#configure test ini
[ -f /srv/ckan/hdx-test-core.ini ] || envsubst < /srv/ckan/docker/hdx-test-core.ini.tpl > /srv/ckan/hdx-test-core.ini

# fix permissions on filestore
mkdir -p /srv/filestore /srv/backup /var/log/ckan
#chown www-data:www-data -R /srv/filestore/
#chown www-data:www-data -R /var/log/ckan
#chown root:root -R /srv/backup
chown -R www-data:www-data /var/log/ckan

# make sure we have the feature-index.js file
lunr_dir=/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search_/lunr
[ -d $lunr_dir ] || mkdir -p $lunr_dir
[ -f $lunr_dir/feature-index.js ] || touch $lunr_dir/feature-index.js

# OPS-6700 -> to be added in the ckan repository
# make sure less compile can write to his folder AND the tmp folder
less_dir=/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/public/css/generated
less_tmp_dir=/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/less/tmp
less_tmp_org_dir=$less_tmp_dir/organization
# chown webassets too
webassets_dir=/srv/webassets

[ -d $less_dir ] || mkdir -p $less_dir
[ -d $less_tmp_org_dir ] || mkdir -p $less_tmp_org_dir
[ -d $webassets_dir ] || mkdir -p $webassets_dir

chown -R www-data $less_dir
chown -R www-data $less_tmp_dir
chown -R www-data $webassets_dir

# make sure cache dir permissions are correct
#chown -R www-data:www-data ${HDX_CACHE_DIR}

#python /srv/ckan/docker/helper.py

# set pgpass if it's not there
#hdxckantool pgpass > /dev/null
# set proper permissions on datastore
#hdxckantool db set-perms > /dev/null

# make ckan dependent on pgb
#sv start pgb || exit 1

#hdxckantool less compile

# build all webassets
hdxckantool webassets
