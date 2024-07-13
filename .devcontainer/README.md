# HDX CKAN VSCode development

## Installation
1. Install and open VSCode
1. Add the "Dev Containers" extension
1. Clone this git repository
1. Open this repo in VSCode
1. Remember to create an `.env.secrets` file in the `.devcontainer` folder from `.env.secrets.template`. Values for secrets can be obtained from OCHA Infrastructure. These secrets also need to be added to `/etc/ckan/prod.ini` in the ckan container.
1. In VS Code click the popup saying "Reopen in container"
1. Wait for an hour while the containers are built and Python packages are installed.
1. The `proxy` network should be produced automatically, if not then run `docker network create proxy` from a shell prompt in the host machine.
1. A value needs to be added to `/etc/ckan/prod.ini` for `beaker.session.secret` inside the ckan container. It does not matter what this value is.
1. Create a `hdx-test-core.ini` file (?) and ensure it has the correct values for the following entries:
```
solr_url = http://solr:8983/solr/ckan
sqlalchemy.url = postgresql://ckan:[secret]@db:5432/ckan_test
ckan.datastore.write_url = postgresql://ckan:[secret]@db:5432/datastore_test
ckan.datastore.read_url = postgresql://datastore:[secret]@db:5432/datastore_test
```

1. The `awscli` commandline tool needs to be installed by running the `awscli-install-run-once.sh` script.

## All-in-one magic one time setup

The "magic" setup prepares the ckan databases and loads them with the latest (minimal) backups, with the `--test` flag databases are prepared but not loaded with data.

1. Type in: `hdxckantool --verbose magic`
1. Type in: `y`, then your jenkins username and password (note that the password characters will not be echoed out in the terminal) - these can be obtained from OCHA Infrastructure;
1. This will take quite a while; go get a few coffees and walks. In the mean time, the following will be done for you (not necessarily in this order):
    1. pull the latest database backups and files backups
    1. restore the files (not filestore)
    1. syncronise the s3 filestore with the dev filestore
    1. [re]create the databases and restores from the last backups
    1. [re]create the solr collection and reindexes it
1.Type in: `hdxckantool --verbose magic --test` - this does similar but does not restore databases or rebuild the solr index
Enjoy!



## Running tests
Once "magic" setup has been carried out, a local instance of the HDX website can be launched with: 

```ckan -c /etc/ckan/prod.ini run --disable-reloader```

VS Code automatically forwards the 5000 port from the ckan container, so that the website can be reached in the host at `localhost:5000`.

Tests are run with commandlines like:

`pytest --ckan-ini=hdx-test-core.ini ./ckanext-hdx_package/ckanext/hdx_package/tests`

This invocation runs 119 test which take about 20 minutes.

## Daily development
1. Note that Desktop Docker starts some of the ckan containers, but not all (solr and zookeeper are not started), on launch so stop them all and allow VS Code to launch them all;
1. Open this repo in VSCode
1. Click the popup saying "Reopen in container"
1. Wait for a bit until the container starts
1. Open a VSCode terminal

Note: All commands shown below are typed in the ckan container; if you do use VSCode Dev Containers, that would be the terminal inside your VSCode



## No magic for me, I want hardcore stuff

### Database Setup
1. The user and database creation is done automatically, but you do need to restore.
1. Set the proper database password in `.pgpass` so you wont have to type it everytime:
    1. Type in: `hdxckantool db pgpass`
1. Make sure the public schema belongs to the database owner:
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
