#!/bin/bash

cd /srv/ckan
ckan -c /etc/ckan/prod.ini db upgrade
ckan -c /etc/ckan/prod.ini db upgrade -p hdx_users
