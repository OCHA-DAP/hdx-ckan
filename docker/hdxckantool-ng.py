#!/usr/bin/env python

import getpass
import os
import subprocess
import sys
import tarfile

import click
import psycopg2
import requests
from bs4 import BeautifulSoup

# import ckan.cli.sysadmin as ckan_sysadmin
# import ckan.cli.user as ckan_user

BASEDIR = os.getenv('HDX_CKAN_BASEDIR', "/srv/ckan")
INI_FILE = os.getenv('INI_FILE', "/etc/ckan/prod.ini")
VERBOSE_INI_FILE = os.getenv('VERBOSE_INI_FILE', "/etc/ckan/less.ini")

SQL = dict(
    HOST=str(os.getenv('HDX_CKANDB_ADDR')),
    PORT='5432',
    SUPERUSER='postgres',
    SUPERPASS=str(os.getenv('POSTGRES_PASSWORD')),
    USER=str(os.getenv('HDX_CKANDB_USER')),
    PASSWORD=str(os.getenv('HDX_CKANDB_PASS')),
    DB=str(os.getenv('HDX_CKANDB_DB')),
    USER_DATASTORE=str(os.getenv('HDX_CKANDB_USER_DATASTORE')),
    DB_DATASTORE=str(os.getenv('HDX_CKANDB_DB_DATASTORE')),
)

SOLR =  dict(
    ADDR = str(os.getenv('HDX_SOLR_ADDR', 'solr')),
    PORT = str(os.getenv('HDX_SOLR_PORT', '8983')),
    CORE = str(os.getenv('HDX_SOLR_CORE', 'ckan')),
    CONFIGSET = str(os.getenv('HDX_SOLR_CONFIGSET', 'hdx-solr'))
)

SNAPSHOTS_TOKEN = None

def db_connect_to_postgres(host=SQL['HOST'], port=SQL['PORT'], dbname=SQL['DB'], user=SQL['USER'], password=SQL['PASSWORD']):
    """connects to postgres"""

    try:
        con = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
        return con
    except:
        raise click.ClickException("I am unable to connect to the database, exiting.")

def db_schema_owner(dbname, schema='public', owner=SQL['USER'], verbose=False):
    """assign a new owner to a schema."""

    try:
        if verbose:
            print("Assigning {} as owner of {} schema of {} database...".format(owner, schema, dbname))
        con = db_connect_to_postgres(dbname=dbname, user=SQL['SUPERUSER'], password=SQL['SUPERPASS'])
        con.set_isolation_level(0)
        cur = con.cursor()
        query = "alter schema {} owner to {};".format(schema, owner)
        cur.execute(query)
        con.commit()
        if verbose:
            print("Done.")
    except:
        raise click.ClickException("I can't assign a new owner")
    finally:
        con.close()



def db_empty(dbname, verbose=False):
    """Recreate the schema for a database."""

    try:
        if verbose:
            print("Flushing database {}...".format(dbname))
        con = db_connect_to_postgres(dbname=dbname)
        con.set_isolation_level(0)
        cur = con.cursor()
        query = "drop schema public cascade; create schema public;"
        cur.execute(query)
        con.commit()
        if verbose:
            print("Done.")
    except:
        raise click.ClickException("I can't flush database {} as {}, try sudo :)".format(dbname, SQL['USER']))
    finally:
        con.close()


def db_query(query):
    try:
        con = db_connect_to_postgres(dbname=SQL['DB'])
        con.set_isolation_level(0)
        cur = con.cursor()
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        raise click.ClickException("I can't query that")
    finally:
        con.close()
    return rows


def sysadmin_exists(user):
    query = "select sysadmin from public.user where name='{}';".format(user)
    rows = db_query(query)
    if len(rows) == 1:
        sysadmin = rows[0][0]
        if sysadmin:
            return True
    return False


def control(cmd):
    flag = dict(
        start="-u",
        stop="-d",
        restart="-r"
    )
    service_folder = '/var/run/s6/services/unit'
    if not os.path.exists(service_folder):
        print("Probably in local environment. Nothing to do.")
        return

    line = ["s6-svc", flag[cmd], service_folder]
    try:
        subprocess.call(line)
    except:
        raise click.ClickException("ckan {} failed.".format(cmd))
        sys.exit(1)


def user_exists(user):
    """Check if user exists."""
    query = "select name,fullname,email,state,sysadmin from public.user where name='{}';".format(user)
    rows = db_query(query)
    if len(rows) == 1:
        return True
    else:
        return False


def user_pretty_list(userlist):
    for row in userlist:
        print('+++++++++++++++++++++++++++++++++++++++++++++++')
        (username, displayname, email, state, sysadmin, apikey) = row
        print('User: {}'.format(username))
        print('Full Name: {}'.format(displayname))
        print('Email: {}'.format(email))
        print('State: {}'.format(state))
        print('Sysadmin: {}'.format(sysadmin))
        print('API Key: {}'.format(apikey))
    print('+++++++++++++++++++++++++++++++++++++++++++++++')
    if len(userlist) > 1:
        print('Got a total of ' + str(len(userlist)) + ' users.')


def get_snapshot_token():
    """Get the authorization token for the snapshots"""
    global SNAPSHOTS_TOKEN
    if SNAPSHOTS_TOKEN:
        return SNAPSHOTS_TOKEN

    args = {
        'grant_type': 'password',
        'client_id': 'token',
        'username': os.getenv('SNAPSHOTS_USERNAME', input('Snapshots username: ')),
        'password': os.getenv('SNAPSHOTS_PASSWORD', getpass.getpass('Snapshots password: '))
    }
    try:
        r = requests.post('https://auth.ahconu.org/oauth2/token', args)
        # print(r.json())
        if 'access_token' in r.json().keys():
            print('Token aquired...')
            SNAPSHOTS_TOKEN = r.json()['access_token']
            return r.json()['access_token']
    except:
        raise click.ClickException('can\'t get the token')


def download(url, headers, filename):
    """Get the requested snapshot file"""
    with open(filename, 'wb') as f:
        response = requests.get(url, headers=headers, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('=' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def get_latest_snapshot_name(url, headers, prefix='prod.min.ckan'):
    """Get the most recent snapshot name"""
    url = 'https://snapshots.aws.ahconu.org/api/hdx/ckan/'
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise click.ClickException("Failed to get the snapshots list from {}".format(url))
    html = r.text
    parsed_html = BeautifulSoup(html, "html.parser")
    a_list = [a.get('href') for a in parsed_html.body.pre.find_all('a') ]
    relevant_list = list(filter(lambda item: item.startswith(prefix), a_list))
    if len(relevant_list) < 1:
        raise click.ClickException("Can't find any item with this prefix ({})".format(prefix))
    relevant_list.reverse()
    return relevant_list[0]


def get_snapshot(prefix):
    token = get_snapshot_token()
    if not token:
        raise click.ClickException('something went wrong. can\'t get the token or something.')
    chunk_size = 4096
    headers = {'Authorization': 'Bearer {}'.format(token)}
    url = 'https://snapshots.aws.ahconu.org/api/hdx/ckan/'

    filename = get_latest_snapshot_name(url, headers, prefix=prefix)

    if filename.startswith('prod.min.ckan') or filename.startswith('prod.ckan'):
        fname = 'ckan.pg_restore'
    elif filename.startswith('prod.datastore'):
        fname = 'datastore.pg_restore'
    else:
        fname = 'files.tar'

    local_file = '/srv/backup/{}'.format(fname)
    print('Getting {} as {}'.format(filename, local_file))
    download('{}{}'.format(url, filename), headers, local_file)


@click.group()
# @click.option('--config', default=INI_FILE, show_default=True, help="Config file to use for ckan cli commands.")
@click.option('-v', '--verbose', is_flag=True, default=False, show_default=True, help="Make ckan cli commands more verbose.")
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = INI_FILE
    ctx.obj['VERBOSE'] = verbose
    if verbose:
        ctx.obj['CONFIG'] = VERBOSE_INI_FILE


@cli.group()
def db():
    """Database related commands."""
    pass

@cli.group()
def files():
    """File assets related commands."""
    pass

@cli.group()
def filestore():
    """S3 filestore related commands."""
    pass

@cli.group()
def solr():
    """SOLR related commands."""
    pass


@cli.command()
def restart():
    """Restart ckan service (gunicorn)."""
    control('restart')


@cli.command()
def start():
    """Start ckan service (gunicorn)."""
    control('start')


@cli.command()
def stop():
    """Stop ckan service (gunicorn)."""
    control('stop')


@cli.group()
def sysadmin():
    """Manage sysadmins."""
    pass


@cli.group()
def user():
    """Manage users."""
    pass


@cli.group()
def token():
    """Manage API tokens."""
    pass


@db.command(name='pgpass')
@click.pass_context
def refresh_pgpass_command(ctx):
    """Make sure the pgpass file is up to date."""
    verbose = ctx.obj['VERBOSE']
    if verbose:
        print("Refreshing .pgpass file...")
    (host, port, user, password)=(SQL['HOST'], SQL['PORT'], SQL['USER'], SQL['PASSWORD'])
    pgpass = '/root/.pgpass'
    correct_line = ':'.join([host, port, '*', user, password])
    super_line = ':'.join([host,port,'*', SQL['SUPERUSER'], SQL['SUPERPASS']])
    newpgpass = [super_line, correct_line]
    with open(pgpass, 'w') as f:
        for line in newpgpass:
            f.write("%s\n" % line)
        if verbose:
            print("File overwritten.")
    if oct(os.stat(pgpass).st_mode)[-3:] != '600':
        os.chmod(pgpass, 0o600)
        if verbose:
            print('Permissions were incorrect. Fixed.')
    if verbose:
        print('Done.')


@db.command(name='pull')
@click.option('-p', '--prefix', default='prod.datastore', show_default=True, help="File name prefix to pull")
@click.option('-a', '--all', is_flag=True, show_default=True, default=False, help="Get _all_ we need (ckan and datastore).")
@click.pass_context
def db_pull(ctx, prefix, all):
    """Pulls the latest database backups from the snapshots site"""
    if not all:
        get_snapshot(prefix)
        return
    prefixes = [ 'prod.datastore', 'prod.min.ckan']
    for p in prefixes:
        get_snapshot(p)


@db.command(name='restore')
@click.option('-S', '--server', default=SQL['HOST'], show_default=True, help="Server to retore to")
@click.option('-d', '--database', default=SQL['DB'], show_default=True, help="Database to restore")
@click.option('-f', '--filename', default='/srv/backup/{}.pg_restore'.format(SQL['DB']), show_default=True, help="File name to restore from")
@click.option('-m', '--minimal', is_flag=True, default=False, show_default=True, help="Skip larger tables (like activity).")
@click.option('-s', '--skip-tables', default='activity,activity_detail,12d7c8e3-eff9-4db0-93b7-726825c4fe9a', show_default=True, help="Skip these specific tables.")
@click.option('-k', '--keep-ckan-running', is_flag=True, show_default=True, default=False, help="Do not stop ckan during restore.")
@click.option('-c', '--clear-database', is_flag=True, show_default=True, default=False, help="Recreate the schema.")
@click.pass_context
def db_restore(ctx, server, database, filename, minimal, skip_tables, keep_ckan_running, clear_database):
    """Restore a database from the backup"""
    # click.echo('{} {}'.format(database,file))
    if not keep_ckan_running:
        print('Stopping ckan ...')
        control('stop')
    else:
        print('Ckan will keep running in the background.')

    restore = "pg_restore -h {} -vOx -n public".format(server).split()
    if clear_database:
        db_empty(database)
        # two hammers should be better than one hammer
        # but you get lots of erros from pg_restore not being able to drop
        # things that were already dropped.
        # you would think it makes send to drop if exists but meh.
        # restore.append('-c')

    skip_tables_data = skip_tables.split(',')
    if minimal:
        print('Restoring minimal database {} from {} ...'.format(database,filename))
        cmd0 = 'pg_restore -l {}'.format(filename).split()
        get_tables = subprocess.check_output(cmd0).decode("utf-8").split('\n')
        schema_only = []
        full_tables = []
        for line in get_tables:
            skip_it = False
            for table in skip_tables_data:
                if "TABLE DATA public {} ".format(table) in line:
                    skip_it = True
                    break
            if skip_it:
                schema_only.append(line)
                continue
            if not len(line):
                continue
            full_tables.append(str(line))
        with open('{}.tables'.format(filename), 'w') as f:
            for line in full_tables:
                f.write('{}\n'.format(str(line)))
        with open('{}.schema_only'.format(filename), 'w') as f:
            for line in schema_only:
                f.write('{}\n'.format(str(line)))
        restore.extend("-U {} -d {} -L {}.tables {}" \
            .format(SQL['USER'], database, filename, filename).split())
    else:
        print('Restoring minimal database {} from {} ...'.format(database,filename))
        restore.extend("-U {} -d {} {}" \
            .format(SQL['USER'], database, filename).split())
    if ctx.obj['VERBOSE']:
        subprocess.call(restore, stderr=subprocess.STDOUT)
    else:
        with open(os.devnull, 'wb') as devnull:
            subprocess.call(restore, stdout=devnull, stderr=subprocess.STDOUT)
    print('Restore completed.')

    if database == SQL['DB_DATASTORE']:
        ctx.invoke(db_set_perms)

    if not keep_ckan_running:
        print('Starting ckan ...')
        control('start')


@db.command(name='schema')
@click.pass_context
def db_set_schema(ctx):
    """Set the owner of the ckan and datastore databases schema"""
    verbose = ctx.obj['VERBOSE']
    db_schema_owner(dbname='datastore', schema='public', owner=SQL['USER'], verbose=verbose)
    db_schema_owner(dbname='ckan', schema='public', owner=SQL['USER'], verbose=verbose)


@db.command(name='perms')
def db_set_perms():
    """Set proper permissions on the ckan and datastore databases"""
    with open('{}/ckanext/datastore/set_permissions.sql'.format(BASEDIR), 'r') as fin:
        query = fin.read() \
            .replace('{mainuser}', SQL['USER']) \
            .replace('{writeuser}', SQL['USER']) \
            .replace('{readuser}', SQL['USER_DATASTORE']) \
            .replace('{maindb}', SQL['DB']) \
            .replace('{datastoredb}', SQL['DB_DATASTORE']) \
            .split('\connect datastore\n')[1]

    try:
        con = db_connect_to_postgres(dbname=SQL['DB_DATASTORE'])
        con.set_isolation_level(0)
        cur = con.cursor()
        cur.execute(query)
        con.commit()
    except:
        raise click.ClickException("Failed to set proper permissions. Exiting.")
    finally:
        con.close()

    print("Datastore permissions have been reset to default.")


@cli.command()
@click.pass_context
def feature(ctx):
    '''Rebuild the feature index.'''
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'hdx-feature-search']
    os.chdir(BASEDIR)
    print('Rebuilding feature index...')
    subprocess.call(cmd)
    print('Fixing permissions on feature-index.js...')
    lunr_folder = os.path.join(BASEDIR, 'ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search_/lunr')
    if os.path.isdir(lunr_folder):
        feature_index_file = os.path.join(lunr_folder,'feature-index.js')
    else:
        feature_index_file = os.path.join(BASEDIR, 'ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search_/lunr/feature-index.js')
    os.chown(feature_index_file, 33, 0)
    print('Done.')


@files.command(name='pull')
@click.option('-p', '--prefix', default='prod.files', show_default=True, help="File name prefix to pull")
@click.pass_context
def files_pull(ctx, prefix):
    """Download the files snapshot."""
    get_snapshot(prefix)


@files.command(name='restore')
@click.option('-f', '--filename', default='/srv/backup/{}.tar'.format('files'), show_default=True, help="File name to restore from")
@click.option('-t', '--targetdir', default='/srv/filestore', show_default=True, help="Target directory to restore in")
@click.pass_context
def files_restore(ctx, filename, targetdir):
    """Unpack the files archive into the targetdir."""
    try:
        with tarfile.open(filename) as t:
            print("Restoring {} content into {} ...".format(filename, targetdir))
            t.extractall(targetdir)
        print("Done.")
    except:
        raise click.ClickException("Can't unpack {} into {}".format(filename, targetdir))


@filestore.command(name='sync')
@click.option('-s', '--source', default='hdx-dev-filestore', show_default=True, help="Source bucket name")
@click.option('-d', '--destination', default='hdx-ckan-inno-filestore', show_default=True, help="Destination bucket name")
@click.option('-x', '--source-region', default='us-east-1', show_default=True, help="Source bucket region")
@click.option('-r', '--region', default='eu-central-1', show_default=True, help="Destination bucket region")
@click.option('-c', '--clear', is_flag=True, show_default=True, default=False, help="Remove differences from the destination bucket.")
@click.pass_context
def filestore_sync(ctx, source, destination, source_region, region, clear):
    """Performs a simple S3 sync"""

    command = ['aws', 's3', 'sync']
    if clear:
        command.append('--delete')
    print("Syncing {} from {} region to {} from {} region...".format(source, source_region, destination, region))
    sync_array = [
        *command,
        's3://{}/'.format(source), 's3://{}/'.format(destination),
        '--source-region', source_region, '--region', region
    ]
    try:
        print(' '.join(sync_array))
        subprocess.check_call(sync_array)
    except:
        raise click.ClickException("S3 sync failed.")


@cli.command(name='less')
@click.argument('compile', required=False)
@click.argument('verbose', required=False)
@click.pass_context
def less_compile(ctx, compile, verbose):
    """Compile the custom stylesheets.

    COMPILE     Deprecated option. Skip it.

    VERBOSE     Deprecated option. Use -v on script level instead.

    """
    click.echo("Deprecated. Don't have any less anymore. Exiting...")
    return
    if compile:
        click.echo("Deprecated argument 'compile'. Just skip it.")
    if verbose:
        click.echo("Deprecated argument 'verbose'. Use -v at script level instead.")
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'custom-less-compile']
    os.chdir(BASEDIR)
    less_wr_dirs = ["ckanext-hdx_theme/ckanext/hdx_theme/public/css/generated", "/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/less/tmp"]
    print('Compiling...')
    subprocess.call(cmd)
    print('Fixing permissions on writeable folders...')
    for location in less_wr_dirs:
        os.chown(location, 33, 0)
        for root, dirs, files in os.walk(os.path.join(BASEDIR, location)):
            for item in dirs:
                os.chown(os.path.join(root, item), 33, 0)
            for item in files:
                os.chown(os.path.join(root, item), 33, 0)
    print('Done.')


@cli.command(name='logs')
def show_logs():
    """Just a glorified tail -f /var/log/ckan/*log"""
    logs = ['/var/log/ckan/access.log', '/var/log/ckan/error.log', '/var/log/ckan/ckan.log']
    cmd = ['tail', '-f']
    cmd.extend(logs)
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('      Stop following the logs with Ctrl+C')
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    subprocess.call(cmd)


@cli.command(name='plugins')
@click.option('-d', '--develop', is_flag=True, default=False, show_default=True, help="Install plugins in develop mode.")
def reinstall_plugins(develop):
    """Reinstall the ckan plugins."""
    path = BASEDIR
    cmd = ['python', 'setup.py']
    if develop:
        cmd.append('develop')
        print('Installing plugins in develop mode.')
    else:
        cmd.append('install')
    for item in os.listdir(path):
        fullpath = os.path.join(path, item)
        if os.path.isdir(fullpath):
            if item.startswith('ckanext-'):
                print('Reinstalling plugin: ', item)
                if os.path.isfile(os.path.join(fullpath, 'setup.py')):
                    os.chdir(fullpath)
                    with open(os.devnull, 'wb') as devnull:
                        subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)



@solr.command(name='add')
@click.option('-h', '--host', default=SOLR['ADDR'], show_default=True, help="SOLR hostname / IP address.")
@click.option('-p', '--port', default=SOLR['PORT'], show_default=True, help="SOLR Port.")
@click.option('-c', '--collection', default=SOLR['CORE'], show_default=True, help="SOLR Collection to add.")
@click.option('-s', '--config-set', default=SOLR['CONFIGSET'], show_default=True, help="SOLR Configset to use.")
@click.option('-f', '--force', is_flag=True, default=False, show_default=True, help="Overwrite collection if exists.")
@click.pass_context
def solr_add(ctx, host, port, collection, config_set, force):
    """Create a SOLR collection"""
    try:
        if ctx.invoke(solr_exists, host=host, port=port, collection=collection):
            if not force:
                print("Collection {} already exists.".format(collection))
                raise click.ClickException("Collection {} already exists. Use --force to forcibly recreate it.".format(collection))
            else:
                ctx.invoke(solr_del)
        query = "http://{}:{}/solr/admin/collections?action=CREATE&name={}&collection.configName={}&numShards=1" \
            .format(host, port, collection, config_set)
        r = requests.get(query)
        if r.status_code != 200:
            raise click.ClickException(r.json()["error"]["msg"])
        print("The collection {} has been created successfully.".format(collection))
    except Exception as e:
        raise click.ClickException("Can't query SOLR: {}".format(str(e)))


@solr.command(name='del')
@click.option('-h', '--host', default=SOLR['ADDR'], show_default=True, help="SOLR hostname / IP address.")
@click.option('-p', '--port', default=SOLR['PORT'], show_default=True, help="SOLR Port.")
@click.option('-c', '--collection', default=SOLR['CORE'], show_default=True, help="SOLR Collection to add.")
@click.pass_context
def solr_del(ctx, host, port, collection):
    """Create a SOLR collection"""
    try:
        if not ctx.invoke(solr_exists, host=host, port=port, collection=collection):
            raise click.ClickException("Collection {} does not exists.".format(collection))
        query = "http://{}:{}/solr/admin/collections?action=DELETE&name={}" \
            .format(host, port, collection)
        r = requests.get(query)
        if r.status_code != 200:
            raise click.ClickException(r.json()["error"]["msg"])
        print("The collection {} has been removed successfully.".format(collection))
    except Exception as e:
        raise click.ClickException("Can't query SOLR: {}".format(str(e)))

@solr.command(name='check')
@click.option('-h', '--host', default=SOLR['ADDR'], show_default=True, help="SOLR hostname / IP address.")
@click.option('-p', '--port', default=SOLR['PORT'], show_default=True, help="SOLR Port.")
@click.option('-c', '--collection', default=SOLR['CORE'], show_default=True, help="SOLR Core (Collection actually).")
def solr_exists(host, port, collection):
    """Check the status of SOLR"""
    try:
        query = "http://{}:{}/solr/admin/collections?action=CLUSTERSTATUS" \
            .format(host, port)
        r = requests.get(query)
        if r.status_code != 200:
            raise click.ClickException(r.json()["error"]["msg"])
        collections = r.json()["cluster"]["collections"].keys()
        if collection not in collections:
            return False
        return True
    except Exception as e:
        raise click.ClickException("Can't query SOLR: {}".format(str(e)))


@solr.command(name='reindex')
@click.option('--clear', is_flag=True, default=False, show_default=True, help="Clear solr index first.")
@click.option('--fast', is_flag=True, default=False, show_default=True, help="Use multiple threaded processes.")
@click.option('--refresh', is_flag=True, default=False, show_default=True, help="Will only refresh. Not usable with fast option.")
@click.pass_context
def solr_reindex(ctx, fast, refresh, clear):
    """Reindex solr."""
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'search-index']
    if clear:
        print("Clearing solr index...")
        subprocess.call(cmd + ['clear'])
    if fast:
        cmd.append('rebuild-fast')
        if refresh:
            print('Ignoring refresh option when doing a fast reindex.')
    else:
        cmd.append('rebuild')
        if refresh:
            cmd.append('-r')
    os.chdir(BASEDIR)
    subprocess.call(cmd)


@sysadmin.command(name='enable')
@click.argument('user')
@click.pass_context
def sysadmin_enable(ctx, user):
    if sysadmin_exists(user):
        print('User ' + user + ' is already sysadmin.')
        sys.exit(0)
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'sysadmin', 'add', user]
    subprocess.call(cmd)


@sysadmin.command(name='disable')
@click.argument('user')
@click.pass_context
def sysadmin_disable(ctx, user):
    if not sysadmin_exists(user):
        print('User ' + user + ' is not sysadmin.')
        sys.exit(0)
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'sysadmin', 'remove', user]
    subprocess.call(cmd)


@sysadmin.command(name='list')
def sysadmin_list():
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where sysadmin='True' order by name asc;"
    rows = db_query(query)
    user_pretty_list(rows)


@token.command(name='add')
@click.argument('user')
@click.argument('name')
@click.argument('expire')
@click.pass_context
def token_add(ctx, user, name, expire):
    """Add a new token for a user.

    USER        Username.

    NAME        New token name.

    EXPIRE      Expires after this many days (max 180).
    """
    if expire > 180:
        print('Maximum token validity is 180 days.')
        sys.exit(0)
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'user', 'token', 'add', user, name, 'expires_in='+str(expire), 'unit=86400']
    subprocess.call(cmd)


@token.command(name='list')
@click.argument('user')
@click.pass_context
def token_list(ctx, user):
    """List tokens belonging to a user.

    USER    The user to list tokens for.
    """
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'user', 'token', 'list', user]
    subprocess.call(cmd)


@token.command(name='revoke')
@click.argument('token_id')
@click.pass_context
def token_revoke(ctx, token_id):
    """Revoke a token.

    TOKEN_ID    The ID of the token to be revoked.
    """
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'user', 'token', 'revoke', token_id]
    subprocess.call(cmd)


@user.command(name='add')
@click.argument('user', type=str)
@click.argument('email', type=str)
@click.argument('password', type=str)
@click.pass_context
def user_add(ctx, user, email, password):
    """Add a new user.

    USER        New user's username.

    EMAIL       New user's email.

    PASSWORD    New user's password.
    """
    (user, email, password) = (str(user), str(email), str(password))
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'user', 'add', str(user), 'email=' + str(email), 'password=' + str(password)]
    try:
        with open(os.devnull, 'wb') as devnull:
            # subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)
            subprocess.check_call(cmd)
        if user_exists(user):
            print('New user has been created:')
            ctx.invoke(user_show, user=user)
    except:
        raise click.ClickException('User %s has not been created' % user)


@user.command(name='list')
def user_list():
    """List all users."""
    query = "select name,fullname,email,state,sysadmin,apikey from public.user order by name asc;"
    rows = db_query(query)
    user_pretty_list(rows)


@user.command(name='search')
@click.argument('string')
def user_search(string):
    """Search users by a partial string.

    STRING  Search users with username containing this string.
    """
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where name like '%{}%';".format(string)
    rows = db_query(query)
    if len(rows) == 0:
        print('No users were found searching for ' + string)
    else:
        user_pretty_list(rows)


@user.command(name='show')
@click.argument('user')
def user_show(user):
    """Show a specific user details.

    USER    Show details for this user.
    """
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where name='{}';".format(user)
    rows = db_query(query)
    user_pretty_list(rows)


@cli.command(name='webassets')
@click.pass_context
def webassets(ctx):
    """Builds the webassts."""

    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'asset', 'build']
    print('Building the webassets...')
    subprocess.call(cmd)
    print('Fixing permissions on writeable folders...')
    # assuming the webassets location is in /srv/webassets...
    location = '/srv/webassets'
    os.chown(location, 33, 0)
    for root, dirs, files in os.walk(location):
        for item in dirs:
            os.chown(os.path.join(root, item), 33, 0)
        for item in files:
            os.chown(os.path.join(root, item), 33, 0)
    print('Done.')

@cli.command(name='magic')
@click.option('-f', '--force', is_flag=True, default=False, show_default=True, help="Just go.")
@click.option('-s', '--solr-config', default=SOLR['CONFIGSET'], show_default=True, help="SOLR configset name")
@click.pass_context
def do_magic(ctx, force, solr_config):
    """Automagically sets things up for you"""

    print('Will do all the initial setup for you. Or just refresh the dbs and files for you')
    print('    - pulls the latest db backup')
    print('    - restores the database')
    print('    - pulls the latest files backup (other than the filestore)')
    print('    - restores the files (other than filestore)')
    print('    - syncronizes the filestore from the dev filestore')
    print('    - creates a new solr collection')
    print('    - reindex solr')
    print('Please be warned this will take quite a while')
    print('    (especially the filestore sync and the solr reindex)')

    if not force:
        whee = input('Do you want to proceed? [y/n]: ')
        if whee not in ['y', 'Y']:
            print('Maybe later then.')
            return

    print('You will be asked to enter your username and password used to get the database snapshots.')
    # pull latest dbs
    ctx.invoke(db_pull, all=True)
    # pull latest files
    ctx.invoke(files_pull)

    # add pgpass
    ctx.invoke(refresh_pgpass_command)
    # fix schemas
    ctx.invoke(db_set_schema)
    # create solr collection
    ctx.invoke(solr_add, force=True, config_set=solr_config) # fix or parametrize this. innovation has 'hdx-solr-main'

    # restore dbs and files
    ctx.invoke(db_restore, database='datastore', filename='/srv/backup/datastore.pg_restore', clear_database=True)
    ctx.invoke(db_restore, database='ckan', filename='/srv/backup/ckan.pg_restore', minimal=True, clear_database=True)
    # fix datastore permissions
    ctx.invoke(db_set_perms)

    # restore files
    ctx.invoke(files_restore, targetdir='/srv/filestore', filename='/srv/backup/files.tar')
    # sync filestore
    ctx.invoke(filestore_sync,
        source='hdx-dev-filestore',
        destination=os.getenv('AWS_BUCKET_NAME'),
        source_region='us-east-1',
        region=os.getenv('REGION_NAME'),
        clear=True)

    # solr reindex time
    ctx.invoke(solr_reindex, clear=True, fast=True)


if __name__ == '__main__':
    cli()
