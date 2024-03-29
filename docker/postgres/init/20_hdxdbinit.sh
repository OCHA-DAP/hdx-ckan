#!/bin/bash

set -e

echo "Creating required users and databases foe HDX ckan..."


psql -v ON_ERROR_STOP=1 --username postgres --dbname postgres <<-EOSQL
	CREATE ROLE $HDX_CKANDB_USER WITH LOGIN PASSWORD '$HDX_CKANDB_PASS';
	CREATE ROLE $HDX_CKANDB_USER_DATASTORE WITH LOGIN PASSWORD '$HDX_CKANDB_PASS_DATASTORE';
	CREATE ROLE $HDX_GISDB_USER WITH LOGIN PASSWORD '$HDX_GISDB_PASS';
	CREATE DATABASE $HDX_CKANDB_DB OWNER $HDX_CKANDB_USER;
	CREATE DATABASE $HDX_CKANDB_DB_DATASTORE OWNER $HDX_CKANDB_USER;
	CREATE DATABASE $HDX_GISDB_DB OWNER $HDX_GISDB_USER;
EOSQL

psql -v ON_ERROR_STOP=1 --username postgres --dbname $HDX_GISDB_DB <<-EOSQL
    CREATE EXTENSION postgis;
    CREATE EXTENSION postgis_topology;
    ALTER SCHEMA topology OWNER TO $HDX_GISDB_USER;
    ALTER TABLE layer OWNER TO $HDX_GISDB_USER;
    ALTER TABLE spatial_ref_sys OWNER TO $HDX_GISDB_USER;
    ALTER TABLE topology OWNER TO $HDX_GISDB_USER;
EOSQL

echo "Done!"
