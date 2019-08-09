#!/bin/sh

# trigger s3 config generate if needed
S3_GENERATE='no'
if [ ! -f /etc/ckan/prod.ini ]; then
    if [ "$S3_FILESTORE" == "enabled" ]; then
        S3_GENERATE='yes'
        echo "We will generate the S3 extra config needed."
    fi
fi

# configure prod.ini
[ -f /etc/ckan/prod.ini ] || envsubst < /srv/ckan/docker/prod.ini.tpl > /etc/ckan/prod.ini
# add s3 config if needed
SF=''
LF='ckan.storage_path = '${HDX_FILESTORE}
if [ "$S3_GENERATE" == "yes" ]; then
    SF=${SF}'ckanext.s3filestore.aws_access_key_id = '${AWS_ACCESS_KEY_ID}'\n'
    SF=${SF}'ckanext.s3filestore.aws_secret_access_key = '${AWS_SECRET_ACCESS_KEY}'\n'
    SF=${SF}'ckanext.s3filestore.aws_bucket_name = '${AWS_BUCKET_NAME}'\n'
    SF=${SF}'ckanext.s3filestore.host_name = http://s3.'${REGION_NAME}'.amazonaws.com\n'
    SF=${SF}'ckanext.s3filestore.region_name= '${REGION_NAME}'\n'
    SF=${SF}'ckanext.s3filestore.signature_version = s3v4\n'
    SF=${SF}$(cat /srv/ckan/common-config-ini.txt | grep -E "^ckan.plugins =")' s3filestore\n'
    SF=${SF}${LF}
    sed -i "s|${LF}|${SF}|" /etc/ckan/prod.ini
fi
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
lunr_dir=/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search/lunr
[ -d $lunr_dir ] || mkdir -p $lunr_dir
[ -f $lunr_dir/feature-index.js ] || touch $lunr_dir/feature-index.js

# make sure cache dir permissions are correct
chown -R www-data:www-data ${HDX_CACHE_DIR}

#python /srv/ckan/docker/helper.py

# set pgpass if it's not there
#hdxckantool pgpass > /dev/null
# set proper permissions on datastore
#hdxckantool db set-perms > /dev/null

# make ckan dependent on pgb
#sv start pgb || exit 1

#hdxckantool less compile
