### HDX CKAN VSCode development

## First Time Setup
1. Install and open VSCode
1. Add the "Dev Containers" extension
1. Clone this git repository
1. Open this repo in VSCode
1. Click the popup saying "Reopen in container"
1. Wait for a few minutes while everything is set up for the first time


## Database Setup
1. The user and database creation is done automatically, but you do need to restore.
1. Pull the latest backups:
    1. In a new terminal inside your VSCode type: `hdxckantool db pull -a`
    1. Type in your user and password used to access the snapshots and jenkins sites; the password will not be echoed out.
1. Restore the ckan and datastore:
    1. Type in: `hdxckantool -v db restore -f /srv/backup/ckan.pg_restore -d ckan -k`
    1. Type in: `hdxckantool -v db restore -f /srv/backup/datastore.pg_restore -d datastore -k`


## Files restore (the ones outside the filestore bucket)
1. Pull the latest backup:
    1. In a new terminal inside your VSCode type: `hdxckantool files pull`
    1. Type in your user and password used to access the snapshots and jenkins sites; the password will not be echoed out.
1. Restore the files: type `hdxckantool files restore`

## First Time Solr Setup
1. Open this repo in VSCode
1. Click the popup saying "Reopen in container"
1. Wait for a bit until the container starts
1. Open a VSCode terminal
    1. Create the solr collection:
        `hdxckantool solr add -s hdx-current -c ckan`
    1. Reindex solr (takes a while. like about 45 minnutes, go for a walk or coffee or both):
        `hdxckantool solr reindex --clear --fast`
