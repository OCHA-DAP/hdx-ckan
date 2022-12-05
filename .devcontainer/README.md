# HDX CKAN VSCode development

## First Time Setup
1. Install and open VSCode
1. Add the "Dev Containers" extension
1. Clone this git repository
1. Open this repo in VSCode
1. Click the popup saying "Reopen in container"
1. Wait for a few minutes while everything is set up for the first time

## Daily development
1. Open this repo in VSCode
1. Click the popup saying "Reopen in container"
1. Wait for a bit until the container starts
1. Open a VSCode terminal

Note: All commands shown below are typed in the ckan container; if you do use VSCode Dev Containers, that would be the terminal inside your VSCode

## All-in-one magic setup
1. Type in: `hdxckantool magic`
1. Type in: `y`, then your jenkins username and password (note that the password characters will not be echoed out in the terminal)
1. This will take quite a while; go get a few coffees and walks. In the mean time, the following will be done for you (not necessarily in this order):
    1. pull the latest database backups and files backups
    1. restore the files (not filestore)
    1. syncronise the s3 filestore with the dev filestore
    1. [re]create the databases and restores from the last backups
    1. [re]create the solr collection and reindexes it
Enjoy!

## No magic for me, I want hardcore stuff

### Database Setup
1. The user and database creation is done automatically, but you do need to restore.
1. Set the proper database password in `.pgpass` so you wont have to type it everytime:
    1. Type in: `hdxckantool db pgpass`
1. Make sure the public schems belongs to the database owner:
    1. Type in: `hdxckantool db schema`
1. Pull the latest backups:
    1. In a new terminal inside your VSCode type: `hdxckantool db pull -a`
    1. Type in your jenkins user and password used; the password will not be echoed out.
1. Restore the ckan and datastore:
    1. Type in: `hdxckantool -v db restore -f /srv/backup/ckan.pg_restore -d ckan -c`
    1. Type in: `hdxckantool -v db restore -f /srv/backup/datastore.pg_restore -d datastore -c`


### Files restore (the ones outside the filestore bucket)
1. Pull the latest backup:
    1. Type in: `hdxckantool files pull`
    1. Type in your jenkins user and password; the password will not be echoed out.
1. Restore the files: type `hdxckantool files restore`

### Solr Setup
1. [Re]create the solr collection:
    `hdxckantool solr add -s hdx-solr -c ckan -f`
1. Reindex solr (takes a while. like about 45 minnutes, go for a walk or coffee or both):
    `hdxckantool solr reindex --clear --fast`

## Sync your S3 filestore
1. Type in: `hdxckantool filestore sync -c`
