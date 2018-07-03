#!/bin/sh

# just for travis, until this PR is merged into dev
# mkdir -p /etc/ckan
# [ -f /etc/ckan/prod.ini.tpl ] || cp -a /srv/ckan/docker/prod.ini.tpl /etc/ckan

# configure prod.ini
[ -f /etc/ckan/prod.ini ] || envsubst < /etc/ckan/prod.ini.tpl > /etc/ckan/prod.ini
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

#python /srv/ckan/docker/helper.py

# set pgpass if it's not there
#hdxckantool pgpass > /dev/null
# set proper permissions on datastore
#hdxckantool db set-perms > /dev/null

# make ckan dependent on pgb
#sv start pgb || exit 1

#hdxckantool less compile
