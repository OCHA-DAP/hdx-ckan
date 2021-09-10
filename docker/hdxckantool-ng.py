import click
import psycopg2
import os
import subprocess
import sys
# import ckan.cli.sysadmin as ckan_sysadmin
# import ckan.cli.user as ckan_user

BASEDIR = os.getenv('HDX_CKAN_BASEDIR', "/srv/ckan")
INI_FILE = os.getenv('INI_FILE', "/etc/ckan/prod.ini")
VERBOSE_INI_FILE = os.getenv('VERBOSE_INI_FILE', "/etc/ckan/less.ini")

SQL = dict(
    HOST=str(os.getenv('HDX_CKANDB_ADDR')),
    PORT='5432',
    USER=str(os.getenv('HDX_CKANDB_USER')),
    PASSWORD=str(os.getenv('HDX_CKANDB_PASS')),
    DB=str(os.getenv('HDX_CKANDB_DB')),
    USER_DATASTORE=str(os.getenv('HDX_CKANDB_USER_DATASTORE')),
    DB_DATASTORE=str(os.getenv('HDX_CKANDB_DB_DATASTORE')),
)


def db_connect_to_postgres(host=SQL['HOST'], port=SQL['PORT'], dbname=SQL['DB'], user=SQL['USER'], password=SQL['PASSWORD']):
    # try:
    con = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
    # except:
    #     print("I am unable to connect to the database, exiting.")
    #     exiting(2)
    return con


def db_empty(dbname):
    """Recreate the schema for a database."""

    try:
        print("Flushing database {}...".format(dbname))
        con = db_connect_to_postgres(dbname=dbname)
        con.set_isolation_level(0)
        cur = con.cursor()
        query = "drop schema public cascade; create schema public;"
        cur.execute(query)
        con.commit()
    except:
        print("I can't flush database {}".format(dbname))
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
        print("I can't query that")
        sys.exit(2)
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
    line = ["s6-svc", flag[cmd], '/var/run/s6/services/ckan']
    try:
        subprocess.call(line)
    except:
        print("ckan {} failed.".format(cmd))
        sys.exit(1)


def user_exists(user):
    """Check if user exists."""
    query = "select name,fullname,email,state,sysadmin from public.user where name='{}';".format(user)
    rows =  (query)
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


@db.command(name='restore')
@click.option('-d', '--database', default=SQL['DB'], show_default=True, help="Database to restore")
@click.option('-f', '--filename', default='/srv/backup/{}.pg_restore'.format(SQL['DB']), show_default=True, help="File name to restore from")
@click.option('-m', '--minimal', is_flag=True, default=False, show_default=True, help="Skip larger tables (like activity).")
@click.option('-s', '--skip-tables', default='activity,activity_detail,12d7c8e3-eff9-4db0-93b7-726825c4fe9a', show_default=True, help="Skip these specific tables.")
@click.option('-k', '--keep-ckan-running', is_flag=True, show_default=True, default=False, help="Do not stop ckan during restore.")
@click.option('-c', '--clear-database', is_flag=True, show_default=True, default=False, help="Recreate the schema.")
@click.pass_context
def db_restore(ctx, database, filename, minimal, skip_tables, keep_ckan_running, clear_database):
    # click.echo('{} {}'.format(database,file))
    if not keep_ckan_running:
        print('Stopping ckan ...')
        control('stop')
    else:
        print('Ckan will keep running in the background.')

    restore = "pg_restore -vOx -n public".split()
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
        get_tables = subprocess.check_output(cmd0).split('\n')
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
            full_tables.append(line)
        with open('{}.tables'.format(filename), 'wb') as f:
            for line in full_tables:
                f.write('{}\n'.format(line))
        with open('{}.schema_only'.format(filename), 'wb') as f:
            for line in schema_only:
                f.write('{}\n'.format(line))
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


@db.command(name='perms')
def db_set_perms():
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
        print("Failed to set proper permissions. Exiting.")
        print(sys.exc_info()[0])
        sys.exit(2)
    finally:
        con.close()

    print("Datastore permissions have been reset to default.")


@cli.command()
@click.pass_context
def feature(ctx):
    '''Rebuild the feature index.'''
    cmd = ['paster', 'hdx-feature-search', 'build', '-c', ctx.obj['CONFIG']]
    os.chdir(os.path.join(BASEDIR, 'ckanext-hdx_search'))
    print('Rebuilding feature index...')
    subprocess.call(cmd)
    print('Fixing permissions on feature-index.js...')
    lunr_folder = os.path.join(BASEDIR, 'ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search_/lunr')
    if os.path.isdir(lunr_folder):
        feature_index_file = os.path.join(lunr_folder,'feature-index.js')
    else:
        feature_index_file = os.path.join(BASEDIR, 'ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search/lunr/feature-index.js')
    os.chown(feature_index_file, 33, 0)
    print('Done.')


@cli.command(name='less')
@click.pass_context
def less_compile(ctx):
    """Compile the custom stylesheets."""
    cmd = ['paster', '--plugin=ckanext-hdx_theme', 'custom-less-compile', '-c', ctx.obj['CONFIG']]
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
@click.argument('deprecated', required=False)
def show_logs(deprecated):
    """Just a glorified tail -f /var/log/ckan/*log

    DEPRECATED      Access logs are now in nginx. No need for this option.
    """
    logs = ['/var/log/ckan/access.log', '/var/log/ckan/error.log', '/var/log/ckan/ckan.log']
    cmd = ['tail', '-f']
    cmd.extend(logs)
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('      Stop following the logs with Ctrl+C')
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    subprocess.call(cmd)


@cli.command(name='pgpass')
@click.pass_context
def refresh_pgpass(ctx):
    """Make sure the pgpass file is up to date."""
    (host, port, user, password)=(SQL['HOST'], SQL['PORT'], SQL['USER'], SQL['PASSWORD'])
    verbose = ctx.obj['VERBOSE']
    pgpass = '/root/.pgpass'
    partial_line = ''.join([':*:', user, ':'])
    correct_line = ':'.join([host, port, '*', user, password])

    newpgpass = []
    if os.path.isfile(pgpass):
        with open(pgpass) as f:
            content = f.readlines()
        for line in content:
            if len(line):   # just skip the empty lines
                line = line.strip()
                if correct_line == line:
                    if verbose:
                        print("The pgpass file has the right content.")
                    # exiting(0)
                    return True
                if partial_line not in line:
                    newpgpass.append(line)
    newpgpass.append(correct_line)
    # print(newpgpass)
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


@cli.command(name='reindex')
@click.option('--clear', is_flag=True, help="Clear solr index first.")
@click.option('--fast', is_flag=True, help="Use multiple threaded processes.")
@click.option('--refresh', is_flag=True, help="Will only refresh. Not usable with fast option.")
@click.pass_context
def solr_reindex(ctx, fast, refresh, clear):
    """Reindex solr."""
    click.echo(ctx.obj['CONFIG'])
    click.echo("{} {} {}".format(fast,refresh,clear))
    cmd = ['ckan', '-c', ctx.obj['CONFIG'], 'search-index']
    if clear:
        print("Clearing solr index...")
        # subprocess.call(cmd + ['clear'])
    if fast:
        cmd.append('rebuild-fast')
        if refresh:
            print('Ignoring refresh option when doing a fast reindex.')
    else:
        cmd.append('rebuild')
        if refresh:
            cmd.append('-r')
    os.chdir(BASEDIR)
    click.echo(' '.join(cmd))
    # subprocess.call(cmd)


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
        print('User %s has not been created' % user)


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


if __name__ == '__main__':
    cli()
