#!/usr/bin/python3

import datetime
import gzip
import psycopg2
import os
import re
import subprocess
import sys
import tarfile

from shutil import rmtree

APP = "ckan"
BASEDIR = "/srv/ckan"
if isinstance(os.getenv('HDX_CKAN_BASEDIR'), str):
    BASEDIR = os.getenv('HDX_CKAN_BASEDIR')
# BRANCH = str(os.getenv('HDX_CKAN_BRANCH'))
BACKUP_AS = 'dev'
if isinstance(os.getenv('HDX_TYPE'), str):
    BACKUP_AS = os.getenv('HDX_TYPE')
INI_FILE = "/srv/prod.ini"
if isinstance(os.getenv('INI_FILE'), str):
    INI_FILE = os.getenv('INI_FILE')

TS = ''

SQL = dict(
    HOST=str(os.getenv('HDX_CKANDB_ADDR')),
    PORT='5432',
    USER=str(os.getenv('HDX_CKANDB_USER')),
    PASSWORD=str(os.getenv('HDX_CKANDB_PASS')),
    DB=str(os.getenv('HDX_CKANDB_DB')),
    USER_DATASTORE=str(os.getenv('HDX_CKANDB_USER_DATASTORE')),
    DB_DATASTORE=str(os.getenv('HDX_CKANDB_DB_DATASTORE')),
    DB_TEST='ckan_test', DB_DATASTORE_TEST='datastore_test'
)

if isinstance(os.getenv('HDX_CKANDB_DB_TEST'), str):
    SQL['DB_TEST'] = os.getenv('HDX_CKANDB_DB_TEST')
if isinstance(os.getenv('HDX_CKANDB_DB_TEST_DATASTORE'), str):
    SQL['DB_DATASTORE_TEST'] = os.getenv('HDX_CKANDB_DB_TEST_DATASTORE')

# to get the snapshot
RESTORE = dict(
    FROM='prod',
    SERVER=str(os.getenv('HDX_BACKUP_SERVER')),
    USER=str(os.getenv('HDX_BACKUP_USER')),
    TMP_DIR='/tmp/ckan-restore'
)

RESTORE['DIR'] = str(os.getenv('HDX_BACKUP_BASE_DIR')) + '/' + RESTORE['FROM']
RESTORE['PREFIX'] = RESTORE['FROM'] + '.' + APP
RESTORE['DB_PREFIX'] = RESTORE['PREFIX'] + '.db'
RESTORE['DB_PREFIX_MAIN'] = RESTORE['DB_PREFIX'] + '.' + SQL['DB']
RESTORE['DB_PREFIX_DATASTORE'] = RESTORE['DB_PREFIX'] + '.' + SQL['DB_DATASTORE']
RESTORE['FILESTORE_PREFIX'] = RESTORE['PREFIX'] + '.filestore'

BACKUP = dict(
    AS=BACKUP_AS,
    DIR='/srv/backup',
    FILESTORE_DIR='/srv/filestore'
)
if isinstance(os.getenv('HDX_BACKUP_DIR'), str):
    BACKUP['DIR'] = os.getenv('HDX_BACKUP_DIR')
if isinstance(os.getenv('HDX_FILESTORE_DIR'), str):
    BACKUP['FILESTORE_DIR'] = os.getenv('HDX_FILESTORE_DIR')
BACKUP['PREFIX'] = BACKUP['AS'] + '.' + APP
BACKUP['DB_PREFIX'] = BACKUP['PREFIX'] + '.db'
BACKUP['DB_PREFIX_MAIN'] = BACKUP['DB_PREFIX'] + '.' + SQL['DB']
BACKUP['DB_PREFIX_DATASTORE'] = BACKUP['DB_PREFIX'] + '.' + SQL['DB_DATASTORE']
BACKUP['FILESTORE_PREFIX'] = BACKUP['PREFIX'] + '.filestore'

SUFFIX = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
TODAY = datetime.datetime.now().strftime('%Y%m%d')
CURRPATH = os.getcwd()


def show_usage():
    doc = """
    Usage:

        hdxckantool CMD [SUBCMD] [OPTIONS]

    Ckan ini file, if not added as last option, defaults to /srv/prod.ini

    Commands, subcommands and options:
        backup [quiet]- backup (optionally no output)
            db        - backup ckan and datastore db
            <wip> gis - backup gis db
            fs        - backup ckan's filestore

        db
            clean     - empty the databases (ckan and datastore)
            set-perms - restore permissions on datastore side
            get       - get latest snapshot of the databases (ckan and datastore)

        deploy        - *DISABLED* just deploy
            test      - *DISABLED* deploy then run tests

        feature       - hdx-feature-search rebuild

        less compile  - compiles less resource defined in prod.ini
            [verbose] - uses less.ini which is more verbose than prod.ini

        log           - shows ALL ckan logs
           noaccess   - shows only error and pain log
           pain       - shows only pain log
           access     - shows only access log
           error      - shows only error log

        pgpass        - create the pgpass entry required to operate on postgres

        plugins       - reinstall plugins

        reindex       - run solr reindex
            [fast]    - run a fast, multicore solr reindex
            [refresh] - only refresh index (do not remove index prior to reindexing)

        restart       - restart ckan service

        restore
            db        - overwrite ckan and datastore db content from the latest snapshot
            fs        - overwrite the filestore content from the latest snapshot
            <wip> gis - overwrite gis db content from the latest snapshot
            cleanup   - remove temporary folder used for restore
            [local]   - restore dbs from local archives

        start         - start ckan service

        stop          - stop ckan service

        sysadmin
            enable    - make a user sysadmin
            disable   - revoke a user's sysadmin privileges

        test          - run nose tests with WARNING loglevel
            DEBUG     - run nose tests with DEBUG loglevel
            INFO      - run nose tests with INFO loglevel
            CRITICAL  - run nose tests with CRITICAL loglevel

        tracking      - update tracking summary

        user
            add       - add user
            delete    - remove user
            search    - search username list for pattern
            show      - show details for a user
            list      - list users
    """
    print(doc)


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def get_input(text='what?', lower=True, empty=''):
    sys.stdout.flush()
    if lower:
        text = text + ' (case insensitive)'
    if empty:
        text = text + ' [' + empty + ']'
    sys.stdout.write(text + ': ')
    result = input().strip()
    if lower:
        result = result.lower()
    if len(result) == 0:
        result = empty
    return result


def control(cmd):
    line = ["sv", cmd, 'ckan']
    try:
        subprocess.call(line)
    except:
        print(cmd + " failed.")
        exiting(1)


def db_submenu():
    # db
    #  clean
    #  get snapshot
    #  overwrite from snapshot
    # print opts
    if len(opts) == 0:
        exiting(1)
    subcmd = opts.pop(0)
    subcmds = ['clean', 'set-perms', 'get']
    if subcmd not in subcmds:
        print(subcmd + ' not implemented yet. Exiting.')
        exiting(1)
    elif subcmd == 'clean':
        print('Dropping and recreating databases!!!')
        if query_yes_no(' Are you sure?', 'no'):
            db_clean()
        else:
            print("Databases are still intact. :)")
            exiting(0)
    elif subcmd == 'set-perms':
        db_set_perms()
    elif subcmd == 'get':
        db_get_last_backups()

    exiting(0)


def db_clean(dbckan=SQL['DB'], dbdatastore=SQL['DB_DATASTORE']):
    for dbname in [dbckan, dbdatastore]:
        print('db_drop(' + dbname + ')')
        db_drop(dbname)
    db_set_perms()


def db_set_perms():
    con = db_connect_to_postgres(dbname=SQL['DB_DATASTORE'])
    cur = con.cursor()
    query_list = [
        'REVOKE CREATE ON SCHEMA public FROM PUBLIC;',
        'REVOKE USAGE ON SCHEMA public FROM PUBLIC;',
        'GRANT CREATE ON SCHEMA public TO ' + SQL['USER'] + ';',
        'GRANT USAGE ON SCHEMA public TO ' + SQL['USER'] + ';',
        'GRANT CREATE ON SCHEMA public TO ' + SQL['USER'] + ';',
        'GRANT USAGE ON SCHEMA public TO ' + SQL['USER'] + ';',
        'REVOKE CONNECT ON DATABASE ' + SQL['DB'] + ' FROM ' + SQL['USER_DATASTORE'] + ';',
        'GRANT CONNECT ON DATABASE ' + SQL['DB_DATASTORE'] + ' TO ' + SQL['USER_DATASTORE'] + ';',
        'GRANT USAGE ON SCHEMA public TO ' + SQL['USER_DATASTORE'] + ';',
        'GRANT SELECT ON ALL TABLES IN SCHEMA public TO ' + SQL['USER_DATASTORE'] + ';',
        'ALTER DEFAULT PRIVILEGES FOR USER ' + SQL['USER'] + ' IN SCHEMA public GRANT SELECT ON TABLES TO ' + SQL['USER_DATASTORE'] + ';'
    ]
    try:
        print('restoring proper permissions on db', SQL['USER_DATASTORE'])
        for query in query_list:
            # print(query)
            cur.execute(query)
        con.commit()
    except:
        print("Failed to set proper permissions. Exiting.")
        exiting(2)
    finally:
        con.close()

    print("Datastore permissions have been reset to default.")


def db_list_backups(listonly=True, ts=TODAY, server=RESTORE['SERVER'], directory=RESTORE['DIR'], user=RESTORE['USER'], ckandb=SQL['DB'], datastoredb=SQL['DB_DATASTORE']):
    print(server)
    print(directory)
    print(RESTORE['DB_PREFIX'])
    if listonly:
        line = ["rsync", '--list-only', user + '@' + server + ':' + directory + '/' + RESTORE['DB_PREFIX'] + '*' + ts + '*']
    else:
        line = ["rsync", "-a", "--progress", user + '@' + server + ':' + directory + '/' + RESTORE['DB_PREFIX'] + '*' + ts + '*', RESTORE['TMP_DIR'] + '/']
        # empty the temp dir first.
        if os.path.isdir(RESTORE['TMP_DIR']):
            rmtree(RESTORE['TMP_DIR'])
        os.makedirs(RESTORE['TMP_DIR'], exist_ok=True)
    # print(str(line))
    try:
        if listonly:
            result = subprocess.check_output(line, stderr=subprocess.STDOUT)
        else:
            result = subprocess.call(line, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print("Can't find archives from", ts, "or can't connect.")
        print('The error encountered was:')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(str(exc.output.decode("utf-8").strip()))
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        q = 'Would you like to search again?'
        if not query_yes_no(q, default='no'):
            print("Aborting restore operation.")
            exiting(0)
        return False
    if listonly:
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print('Listing backups found:')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        result = result.decode("utf-8").rstrip('\n\n')
        print(("Output: \n{}\n".format(result)))
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
    return result


def db_get_last_backups():
    list = db_list_backups().split('\n')
    list_db = []
    list_db_datastore = []
    for line in list:
        name = line.split()[4]
        # print(name)
        if name.startswith(RESTORE['DB_PREFIX'] + '.' + SQL['DB']):
            list_db.append(name)
        elif name.startswith(RESTORE['DB_PREFIX'] + '.' + SQL['DB_DATASTORE']):
            list_db_datastore.append(name)
    # print(list_db)
    # print(list_db_datastore)
    backup = []
    ts = ''
    for db_name in list_db:
        # print(db_name)
        ts = db_name.split('.')[4]
        for db_datastore_name in list_db_datastore:
            # print(db_datastore_name)
            if db_datastore_name.endswith(ts + '.plsql.gz'):
                backup.append(db_name)
                backup.append(db_datastore_name)
                break
        else:
            continue
        break
    if len(backup) != 2:
        print("Can't figure out a pair of main ckan db and datastore db having the same timestamps. Aborting...")
        exiting(0)
    print('Trying to get for you the following backups:')
    print(backup[0])
    print(backup[1])
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
    db_list_backups(False, ts)
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('Done. Backups are available in', RESTORE['TMP_DIR'])
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
    global TS
    TS = ts


def dbs_restore(from_local):
    q = 'Are you sure you want to overwrite ckan databases? '
    if not query_yes_no(q, default='no'):
        print("Aborting restore operation.")
        exiting(0)
    # print(from_local)
    if not from_local:
        db_get_last_backups()
    # unzip the files
    control('stop')
    for file in os.listdir(RESTORE['TMP_DIR']):
        archive_full_path = os.path.join(RESTORE['TMP_DIR'], file)
        print(archive_full_path)
        file_full_path = archive_full_path.replace('.gz', '')
        decompress_file(archive_full_path, file_full_path, False)
        if file.startswith(RESTORE['DB_PREFIX'] + '.' + SQL['DB']):
            # restore main db
            db_restore(filename=file_full_path, db=SQL['DB'])
        elif file.startswith(RESTORE['DB_PREFIX'] + '.' + SQL['DB_DATASTORE']):
            # restore datastore db
            db_restore(filename=file_full_path, db=SQL['DB_DATASTORE'])
            # restore permissions on datastore db
            db_set_perms()
        else:
            print("I don't know what to do with the file", file)
            print('Skipping...')
    control('start')


def db_restore(host=SQL['HOST'], port=SQL['PORT'], user=SQL['USER'], db='', prefix='', verbose=True, filename=''):
    if not filename or not db:
        print('No filename to restore from or no db found. Aborting...')
        exiting(0)
    print('Please wait. This may take a while...')
    db_drop(db)
    db_create(db)
    print('Restoring database', db, 'from', filename)
    print('Please wait. This may take a while...')
    cmd = ['pg_restore', '-vOx', '-h', host, '-p', port, '-U', user, '-d', db, filename]
    # print(cmd)
    with open(os.devnull, 'wb') as devnull:
        subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)


def backup_db(host=SQL['HOST'], port=SQL['PORT'], user=SQL['USER'], db='', prefix='', verbose=True):
    if not db or not prefix:
        print('backup_db called with empty archive or prefix')
        exiting(0)
    # backup main db
    if not os.path.isdir(BACKUP['DIR']):
        print('Backup directory (' + BACKUP['DIR'] + ') does not exists.')
        exiting(0)
    archive_name = BACKUP['DIR'] + '/' + prefix + '.' + db + '.' + SUFFIX + '.plsql'
    if verbose:
        sys.stdout.write('Archiving ' + db + ' db under ' + archive_name + '.gz\n')
    sys.stdout.flush()
    try:
        cmd = 'pg_dump -vFt -h ' + host + ' -p ' + port + ' -U ' + user + ' -f  ' + archive_name + ' ' + db
        with open(os.devnull, 'wb') as devnull:
            subprocess.call(cmd.split(), stdout=devnull, stderr=subprocess.STDOUT)
    except IOError:
        sys.stdout.write('Error on ' + db + ' db backup... Please try again.\n')
        sys.stdout.flush()
    else:
        if os.path.isfile(archive_name):
            # compress it
            if verbose:
                sys.stdout.write('compressing ' + archive_name + '\n')
                sys.stdout.flush()
            compress_file(archive_name, remove=True)
        else:
            sys.stdout.write(archive_name + ' not found\n')
            sys.stdout.flush()


def backup_filestore(verbose=True):
    # backup filestore
    if not os.path.isdir(BACKUP['DIR']):
        print('Backup directory (' + BACKUP['DIR'] + ') does not exists.')
        exiting(0)
    filestore_archive = BACKUP['DIR'] + '/' + BACKUP['FILESTORE_PREFIX'] + '.' + SUFFIX + '.tar'
    if verbose:
        sys.stdout.write('Archiving filestore from ' + BACKUP['FILESTORE_DIR'] + ' under ' + filestore_archive + '\n')
        sys.stdout.flush()
    try:
        tar = tarfile.open(filestore_archive, 'w')
        os.chdir(BACKUP['FILESTORE_DIR'])
        # print(os.listdir('.'))
        # print(os.cwd())
        for folder in ['storage', 'resources']:
            if os.path.isdir(folder):
                tar.add(folder)
            else:
                raise NameError('filestore backup:', 'folder "' + folder + '" not found under ' + BACKUP['FILESTORE_DIR'])
        # tar.add('storage')
        tar.add('test')
        # tar.add('.', arcname='filestore')
    except IOError:
        sys.stdout.write('Filestore content changed while I was reading it... Please try again.\n')
        sys.stdout.flush()
        exiting(0)
    except NameError as err:
        phase, reason = err.args
        sys.stdout.write('An error has occured: ' + reason + '\n')
        sys.stdout.flush()
        exiting(0)
    else:
        tar.close()
        if verbose:
            sys.stdout.write('compressing ' + filestore_archive + '\n')
            sys.stdout.flush()
        if os.path.isfile(filestore_archive):
            # compress it
            compress_file(filestore_archive, remove=True)
        else:
            sys.stdout.write(filestore_archive + 'not found\n')
            sys.stdout.flush()
            exiting(0)


def decompress_file(f_in='', f_out='', remove=False):
    if not f_in:
        return False
    if not f_out:
        f_out = f_in.replace('.gz', '', 1)
    try:
        with gzip.open(f_in, 'rb') as file_in:
            with open(f_out, 'wb') as file_out:
                file_out.writelines(file_in)
    except IOError:
        sys.stdout.write('Error decompressing ' + f_in + ' ... Please try again.\n')
        sys.stdout.flush()
    else:
        if remove:
            # print(f_in)
            os.remove(f_in)


def compress_file(f_in='', f_out='', remove=False):
    if not f_in:
        return False
    if not f_out:
        f_out = f_in + '.gz'
    try:
        with open(f_in, 'rb') as file_in:
            with gzip.open(f_out, 'wb') as file_out:
                file_out.writelines(file_in)
    except IOError:
        sys.stdout.write('Error compressing ' + f_in + ' ... Please try again.\n')
        sys.stdout.flush()
    else:
        if remove:
            # print(f_in)
            os.remove(f_in)


def db_test_refresh():
    for dbname in [SQL['DB_TEST'], SQL['DB_DATASTORE_TEST']]:
        # db_drop(dbname)
        # db_create(dbname)
        db_empty(dbname)


def db_connect_to_postgres(host=SQL['HOST'], port=SQL['PORT'], dbname=SQL['DB'], user=SQL['USER'], password=SQL['PASSWORD']):
    # try:
    con = psycopg2.connect(host=host, port=port, database=dbname, user=user, password=password)
    # except:
    #     print("I am unable to connect to the database, exiting.")
    #     exiting(2)
    return con


def db_empty(dbname):
    '''removes all tables from a database'''
    try:
        con = db_connect_to_postgres(dbname=dbname)
    except:
        print("Can't connect to the database" + dbname)
        con.close()
        exiting(2)

    #con.set_isolation_level(0)
    cur = con.cursor()
    drop_db = 'drop schema public cascade; create schema public;'
    # print(drop_db)

    try:
        cur.execute(drop_db)
        print('Database ' + dbname + ' has been flushed.')
    except:
        print("I can't flush database " + dbname)
    finally:
        con.close()


def db_drop(dbname):
    con = db_connect_to_postgres()
    con.set_isolation_level(0)
    cur = con.cursor()
    drop_db = 'DROP DATABASE IF EXISTS ' + dbname
    # print(drop_db)
    try:
        cur.execute(drop_db)
        print('Database ' + dbname + ' has been dropped.')
    except:
        print("I can't drop database " + dbname)
    finally:
        con.close()


def db_create(dbname, owner=SQL['USER']):
    # list databases
    # SELECT datname FROM pg_database
    # WHERE datistemplate = false;
    con = db_connect_to_postgres()
    con.set_isolation_level(0)
    cur = con.cursor()
    create_db = 'CREATE DATABASE ' + dbname + ' OWNER ' + owner
    options = " ENCODING 'UTF-8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8'"
    # print(create_db + options)
    cur.execute(create_db + options)
    # try:
    #     cur.execute(create_db + options)
    #     print('Database ' + dbname + ' has been created.')
    # except:
    #     print("I can't create database " + dbname)
    #     exiting(2)
    # finally:
    #     con.close()


# def deploy():
#     control('stop')
#     print('changing dir to', BASEDIR)
#     os.chdir(BASEDIR)
#     #print('fetching branch or tag', BRANCH)
#     #cmd_line = ['git', 'fetch', 'origin', BRANCH]
#     print('fetching branches and tags')
#     cmd_line = ['git', 'fetch']
#     subprocess.call(cmd_line)
#     print('hopping onto', BRANCH)
#     cmd_line = ['git', 'checkout', BRANCH]
#     subprocess.call(cmd_line)
#     print("pulling latest changes of ", BRANCH)
#     cmd_line = ['git', 'pull', 'origin', BRANCH]
#     subprocess.call(cmd_line)
#     print('done. starting', APP)
#     control('start')
#     if (len(opts) != 0) and (opts[0] == 'test'):
#         tests()


def feature():
    '''rebuilds the feature-index.js'''
    cmd = ['ckan', '-c', INI_FILE, 'hdx-feature-search']
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


def filestore_restore(ts=TODAY, server=RESTORE['SERVER'], directory=RESTORE['DIR'], user=RESTORE['USER'], clean=False):
    # print('This doesn\'t do anything right now...')
    # exiting(0)
    line = ["rsync", "-a", "--progress", user + '@' + server + ':' + directory + '/' + RESTORE['FILESTORE_PREFIX'] + '*' + ts + '*', RESTORE['TMP_DIR'] + '/']
    # if os.path.isdir(RESTORE['TMP_DIR']):
    #     for the_file in os.listdir(RESTORE['TMP_DIR']):
    #         file_path = os.path.join(RESTORE['TMP_DIR'], the_file)
    #         try:
    #             # if os.path.isfile(file_path):
    #             os.unlink(file_path)
    #         except Exception as e:
    #             print(e)
    #     #rmtree(RESTORE['TMP_DIR'])
    # else:
    os.makedirs(RESTORE['TMP_DIR'], exist_ok=True)
    print('Getting the filestore archive...')
    try:
        result = subprocess.call(line, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print("Can't find archive from", ts, "or can't connect.")
        print('The error encountered was:')
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        print(str(exc.output.decode("utf-8").strip()))
        print('+++++++++++++++++++++++++++++++++++++++++++++++++++++')
        # q = 'Would you like to get anothr backup?'
        # if not query_yes_no(q, default='no'):
        #     print("Aborting restore operation.")
        #     exiting(0)
        print('try another timestamp')
        return False
    print('Done.')
    #tfilename =  os.path.join(RESTORE['TMP_DIR'], os.listdir(RESTORE['TMP_DIR'])[0])
    # changed per Steven Merrill suggestion
    tf = []
    for f in os.listdir(RESTORE['TMP_DIR']):
        if re.search('.tar.gz$', f):
            tf.append(f)
    #tf = [f in os.listdir(RESTORE['TMP_DIR']) if re.search('.tpl$', f)]
    tfilename = os.path.join(RESTORE['TMP_DIR'], tf[0])
    if tarfile.is_tarfile(tfilename):
        if clean:
            filestore_dir = BACKUP['FILESTORE_DIR']
            for root, dirs, files in os.walk(filestore_dir, topdown=False):
                for item in files:
                    try:
                        os.remove(os.path.join(root, item))
                    except Exception as e:
                        print(e)
                        print('error removing ' + item)
                if root != filestore_dir:
                    try:
                        os.rmdir(root)
                    except Exception as e:
                        print(e)
                        print('error removing ' + root)

                        # for the_file in os.listdir(filestore_dir):
            #     file_path = os.path.join(filestore_dir, the_file)
            #     try:
                    # if os.path.isfile(file_path):
                    # os.unlink(file_path)
                # except Exception as e:
                #     print(e)
            # rmtree('/srv/filestore')
            # os.makedirs('/srv/filestore', exist_ok=True)
            # exiting(0)
        tfile = tarfile.open(tfilename, 'r:gz')
        print('Restoring filestore from ' + tfilename)
        print('It will take a while...')
        try:
            tfile.extractall('/srv')
        except:
            print('some error occured. bailing out...')
            exiting(0)
    else:
        print(tfilename + ' is not a valid archive.')
        exiting(0)
    print('Fixing permissions on filestore')
    for root, dirs, files in os.walk(BACKUP['FILESTORE_DIR']):
        for item in dirs:
            os.chown(os.path.join(root, item), 33, 33)
            os.chmod(os.path.join(root, item), 0o755)
        for item in files:
            os.chown(os.path.join(root, item), 33, 33)
            os.chmod(os.path.join(root, item), 0o644)
    print('All done! Please do not forget to remove the archives in ' + RESTORE['TMP_DIR'])


def gis_init():
    gis_envs = ['HDX_GISDB_ADDR', 'HDX_GISDB_PORT', 'HDX_GISDB_DB', 'HDX_GISDB_USER', 'HDX_GISDB_PASS']
    gis_db_details = []
    for env in gis_envs:
        if isinstance(os.getenv(env), str):
            gis_db_details.append(os.getenv(env))
        else:
            print('Error. Env var', env, 'not found. Exiting.\n')
            exiting(0)
    return gis_db_details


def gis_db_clear():
    '''empty the gis database'''

    if not query_yes_no('Clearing gis db. Are you sure?', default='no'):
        print('Nothing changed.')
        exiting(0)

    host, port, db, user, password = gis_init()
    refresh_pgpass(host=host, port=port, user=user, password=password, verbose=False)
    # psql -h $HDX_GISDB_ADDR -p $HDX_GISDB_PORT -U $HDX_GISDB_USER $HDX_GISDB_DB -ntc '\dt' | awk -F \|
    # '{ print $2 }' | sed -e 's/^ //g' | grep -E "^pre_" | more
    con = db_connect_to_postgres(host=host, port=port, user=user, dbname=db)
    con.set_isolation_level(0)
    cur = con.cursor()

    cur.execute('DROP EXTENSION postgis CASCADE;')

    try:
        query = "SELECT table_name, table_type FROM information_schema.tables WHERE table_schema = 'public';"
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
        if len(rows) > 1:
            print('Removing', len(rows), 'tables...')
        for row in rows:
            table_name, table_type = row
            if table_type == 'BASE TABLE':
                query = "DROP TABLE " + row[0] + " CASCADE;"
                cur.execute(query)
            else:
                print('Not a table... What could it be?. Skipping.')

        cur.execute('CREATE EXTENSION postgis;')
        cur.execute('CREATE EXTENSION postgis_topology;')

    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()


def gis_restore():
    gis_db_clear()
    host, port, db, user, password = gis_init()

    archive_name = '/srv/backup/gis.plsql.gz'
    filename = '/srv/backup/gis.plsql'

    decompress_file(archive_name, filename, False)

    print('Restoring database', db, 'from', filename)
    print('Please wait. This may take a while...')
    cmd = ['pg_restore', '-vOx', '-h', host, '-p', port, '-U', user, '-d', db, filename]
    # print(cmd)
    with open(os.devnull, 'wb') as devnull:
        subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)
    db_restore(host=host, port=port, user=user, db=db, filename='/srv/backup/gis.psql')


def gis_backup(verbose=True):
    '''wrapper for backup_db for now'''
    host, port, db, user, password = gis_init()
    refresh_pgpass(host=host, port=port, user=user, password=password, verbose=False)
    backup_db(host=host, port=port, user=user, db=db, prefix=BACKUP['DB_PREFIX'], verbose=True)


def less_compile(verbose=False):
    if verbose:
        ini_file = '/etc/ckan/less.ini'
    else:
        ini_file = INI_FILE
    cmd = ['ckan', '-c', ini_file, 'custom-less-compile']
    os.chdir(BASEDIR)
    less_wr_dirs = ["ckanext-hdx_theme/ckanext/hdx_theme/public/css/generated", "/srv/ckan/ckanext-hdx_theme/ckanext/hdx_theme/less/tmp"]
    # for location in less_wr_dirs:
    os.makedirs(RESTORE['TMP_DIR'], exist_ok=True)
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


def refresh_pgpass(host=SQL['HOST'], port=SQL['PORT'], user=SQL['USER'], password=SQL['PASSWORD'], verbose=True):

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


def reinstall_plugins():
    path = BASEDIR
    cmd = ['python', 'setup.py']
    if len(opts) == 1:
        if opts.pop(0) in ['dev', 'develop']:
            cmd.append('develop')
    if len(cmd) == 2:
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


def restore_cleanup():
    print('Cleaning up temporary directory used for restore (' + RESTORE['TMP_DIR'] + ')')
    if os.path.isdir(RESTORE['TMP_DIR']):
        rmtree(RESTORE['TMP_DIR'])
    print('Done.')


def solr_reindex():
    valid_subcommands = ['fast', 'refresh']
    cmd = ['ckan', 'search-index']
    cmd_suffix = ['rebuild', '-c', INI_FILE]
    while len(valid_subcommands) > 0:
        if len(opts) > 0:
            subcmd = opts.pop(0)
        else:
            break
        if subcmd in valid_subcommands:
            if subcmd == 'fast':
                cmd_suffix.pop(0)
                cmd_suffix.insert(0, 'rebuild_fast')
            if subcmd == 'refresh':
                cmd.append('-r')
            valid_subcommands.remove(subcmd)
    cmd.extend(cmd_suffix)
    os.chdir(BASEDIR)
    subprocess.call(cmd)


def show_logs():
    logs = ['/var/log/ckan/access.log', '/var/log/ckan/error.log', '/var/log/ckan/ckan.log']
    if len(opts) == 1:
        opt = opts.pop(0)
        if opt == 'noaccess':
            logs.pop(0)
        elif opt == 'pain':
            logs.pop(0)
            logs.pop(0)
        elif opt == 'access':
            logs.pop(-1)
            logs.pop(-1)
        elif opt == 'error':
            logs.pop(0)
            logs.pop(-1)
    cmd = ['tail', '-f']
    cmd.extend(logs)
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    print('      Stop following the logs with Ctrl+C')
    print('+++++++++++++++++++++++++++++++++++++++++++++++++++')
    subprocess.call(cmd)


def sysadmin():
    if len(opts) == 0:
        exiting(1)
    subcmd = opts.pop(0)
    subcmds = ['enable', 'disable', 'list']
    if subcmd not in subcmds:
        print(subcmd + ' not implemented yet. Exiting.')
        exiting(1)
    if subcmd == 'list':
        sysadmins_list()
        exiting(0)
    if len(opts) == 0:
        print('No user has been specified. Exiting.')
        exiting(1)
    user = opts.pop(0)
    if not user_exists(user):
        print('User ' + user + ' has not been found.')
        exiting(1)
    if subcmd == 'enable':
        sysadmin_enable(user)
    else:
        sysadmin_disable(user)


def sysadmin_enable(user):
    if is_sysadmin(user):
        print('User ' + user + ' is already sysadmin.')
        exiting(0)
    cmd = ['ckan', 'sysadmin', 'add', user]
    os.chdir(BASEDIR)
    subprocess.call(cmd)
    exiting(0)


def sysadmin_disable(user):
    if not is_sysadmin(user):
        print('User ' + user + ' is not sysadmin.')
        exiting(0)
    cmd = ['ckan', 'sysadmin', 'remove', user]
    os.chdir(BASEDIR)
    subprocess.call(cmd)
    exiting(0)


def sysadmins_list():
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where sysadmin='True' order by name asc;"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()

    user_pretty_list(rows)
    exiting(0)


def is_sysadmin(user):
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select sysadmin from public.user where name='" + user + "';"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()
    if len(rows) == 1:
        sysadmin = rows[0][0]
        if sysadmin:
            return True
    return False


def tests():
    db_test_refresh()
    os.chdir(BASEDIR)
    # get hdx plugin list
    dirs = sorted(os.listdir('.'))
    res = 0
    for dirname in dirs:
        if dirname.startswith('ckanext-hdx_'):
            print("++++++++++++++++++++++++++++++++++++++++++++++++++++")
            print("Running tests for plugin", dirname)
            res += tests_nose(dirname)
    if res:
        print(" FAILURES: ", res)
    exit(res)


def tests_nose(dirname):
    plugin = dirname.replace('ckanext-', '')
    loglevel = 'WARNING'
    if len(opts) == 1:
        opt = opts.pop(0)
        if opt in ['DEBUG', 'INFO', 'CRITICAL']:
            loglevel = opt
    test_call = [
        'nosetests', '-ckan', dirname + '/ckanext/' + plugin + '/tests',
        '--with-xunit', '--xunit-file=' + dirname + '/ckanext/' + plugin + '/tests/nose_results.xml',
        '--logging-level', loglevel,
        '--with-pylons=' + dirname + '/test.ini.sample',
        '--with-coverage', '--cover-package=ckanext.' + plugin
    ]
    os.chdir(BASEDIR)
    # I need to return this for jenkins
    return subprocess.call(test_call)


def tracking_update():
    cmd = ['paster', 'tracking', 'update', '-c', INI_FILE]
    os.chdir(BASEDIR)
    subprocess.call(cmd)


def users():
    if len(opts) == 0:
        exiting(1)
    subcmd = opts.pop(0)
    subcmds = ['add', 'delete', 'list', 'search', 'show']
    if subcmd not in subcmds:
        print(subcmd + ' not implemented yet. Exiting.')
        exiting(1)
    if subcmd == 'list':
        users_list()
        exiting(0)
    if len(opts) == 0:
        print('No user has been specified. Exiting.')
        exiting(1)
    user = opts.pop(0)
    if subcmd == 'add':
        if user_exists(user):
            print('User ' + user + ' already exists.')
        else:
            user_add(user)
    elif subcmd == 'delete':
        if not user_exists(user):
            print('User ' + user + ' has not been found.')
        else:
            user_delete(user)
    elif subcmd == 'show':
        if not user_exists(user):
            print('User ' + user + ' has not been found.')
        else:
            user_show(user)
    elif subcmd == 'search':
        user_search(user)
    exiting(0)


def users_list():
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select name,fullname,email,state,sysadmin from public.user order by name asc;"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()

    user_pretty_list(rows)


def user_show(user):
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where name='" + user + "';"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()

    user_pretty_list(rows)


def user_search(user):
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select name,fullname,email,state,sysadmin,apikey from public.user where name like '%" + user + "%';"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()
    if len(rows) == 0:
        print('No users were found searching for ' + user)
        exiting(0)
    user_pretty_list(rows)


def user_add(user):
    email = get_input('Email')
    password = get_input('Password', lower=False)
    cmd = ['ckan', 'user', 'add', user, 'email=' + email, 'password=' + password]
    os.chdir(BASEDIR)
    with open(os.devnull, 'wb') as devnull:
        subprocess.call(cmd, stdout=devnull, stderr=subprocess.STDOUT)
    if user_exists(user):
        print('New user has been created:')
        user_show(user)
    else:
        print('I could not create the user ' + user)
    exiting(0)


def user_delete(user):
    if is_sysadmin(user):
        sysadmin_disable(user)
    cmd = ['ckan', 'user', 'remove', user]
    os.chdir(BASEDIR)
    subprocess.call(cmd)


def user_pretty_list(userlist):
    for row in userlist:
        print('+++++++++++++++++++++++++++++++++++++++++++++++')
        (username, displayname, email, state, sysadmin, apikey) = row
        print('User: ' + str(username))
        print('Full Name: ' + str(displayname))
        print('Email: ' + str(email))
        print('State: ' + str(state))
        print('Sysadmin: ' + str(sysadmin))
        print('API Key: ' + str(apikey))
    print('+++++++++++++++++++++++++++++++++++++++++++++++')
    if len(userlist) > 1:
        print('Got a total of ' + str(len(userlist)) + ' users.')


def user_exists(user):
    con = db_connect_to_postgres(dbname=SQL['DB'])
    con.set_isolation_level(0)
    cur = con.cursor()
    query = "select name,fullname,email,state,sysadmin from public.user where name='" + user + "';"
    try:
        cur.execute(query)
        con.commit()
        rows = cur.fetchall()
    except:
        print("I can't query that")
        exiting(2)
    finally:
        con.close()

    if len(rows) == 1:
        return True
    else:
        return False


def exiting(code=0):
    if code == 1:
        show_usage()
    os.chdir(CURRPATH)
    sys.exit(code)


def main():
    cmd = opts.pop(0)
    no_subcommands_list = ['restart', 'start', 'status', 'stop']
    if cmd == 'db':
        db_submenu()
    # elif cmd == 'deploy':
    #     deploy()
    elif cmd == 'feature':
        feature()
    elif cmd == 'pgpass':
        refresh_pgpass()
        host, port, db, user, password = gis_init()
        refresh_pgpass(host=host, port=port, user=user, password=password)
    elif cmd == 'backup':
        if 'quiet' in opts:
            opts.remove('quiet')
            verbose = False
        else:
            verbose = True
        if len(opts):
            if opts[0] == 'db':
                refresh_pgpass(host=SQL['HOST'], port=SQL['PORT'], user=SQL['USER'],
                               password=SQL['PASSWORD'], verbose=False)
                backup_db(db=SQL['DB'], prefix=BACKUP['DB_PREFIX'], verbose=verbose)
                backup_db(db=SQL['DB_DATASTORE'], prefix=BACKUP['DB_PREFIX'], verbose=verbose)
            elif opts[0] == 'fs':
                backup_filestore(verbose)
            elif opts[0] == 'gis':
                gis_backup()
            else:
                exiting(1)
        else:
            exiting(1)
    elif cmd in no_subcommands_list:
        control(cmd)
    elif cmd == 'reindex':
        solr_reindex()
    # elif cmd == 'filestore':
    #     if len(opts) and opts[0] == 'restore':
    #         if len(opts) > 1 and opts[1] == 'clean':
    #             filestore_restore(clean=True)
    #         else:
    #             filestore_restore()
    elif cmd == 'plugins':
        reinstall_plugins()
    elif cmd == 'restore':
        if len(opts):
            from_local = False
            if 'local' in opts:
                opts.remove('local')
                from_local = True
            if opts[0] == 'db':
                dbs_restore(from_local)
            elif opts[0] == 'fs':
                filestore_restore()
            elif opts[0] == 'gis':
                gis_restore()
                # print('gis restore not yet implemented')
            elif opts[0] == 'cleanup':
                restore_cleanup()
            else:
                exiting(1)
        else:
            exiting(1)
    elif cmd == 'less':
        if len(opts) >= 1 and 'compile' in opts:
            if 'verbose' in opts:
                less_compile(verbose=True)
            else:
                less_compile()
        else:
            exiting(1)
    elif cmd == 'log':
        show_logs()
    elif cmd == 'sysadmin':
        sysadmin()
    elif cmd == 'test':
        tests()
    elif cmd == 'tracking':
        tracking_update()
    elif cmd == 'user':
        users()
    else:
        exiting(1)


if __name__ == '__main__':
    opts = sys.argv
    script = opts.pop(0)
    # print(os.path.realpath(__file__))
    if len(opts) == 0:
        exiting(1)
    main()
