import ckan.plugins as p
import os
from ckan.model import Session
import requests
import time
from urlparse import urlparse
from ckan.lib.uploader import ResourceUpload


class MigrateCommand(p.toolkit.CkanCommand):
    '''
    Usage:
        paster hdx-migrate filestore
        - migrate filestore from 2.1 to 2.2
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(MigrateCommand, self).__init__(name)

    def command(self):
        if not self.args or self.args[0] in ['-h', '--help', 'help'] or not len(self.args) in [1, 2]:
            print self.usage
            return

        cmd = self.args[0]
        self._load_config(load_site_user=False)
        if cmd == 'filestore':
            print 'Initializing Migration...'
            self.migrate()
            print 'DONE Migrating Filestore...'
        else:
            print 'Error: command "{0}" not recognized'.format(cmd)
            print self.usage

    def migrate(self):
        '''
        Migrate filestore over in our very HDXish way :)
        '''
        results = Session.execute("select id, revision_id, url from resource "
                                  "where resource_type = 'file.upload' "
                                  "and (url_type <> 'upload' or url_type is null)"
                                  "and url like '%storage%'")
        for id, revision_id, url in results:
            print 'Give it a second, would you?'
            time.sleep(1)
            url_parts = urlparse(url)
            url_parts = url_parts.path.split("/")
            filename = url_parts[len(url_parts)-1]
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                print "failed to fetch %s (code %s)" % (url,
                                                        response.status_code)
                continue
            resource_upload = ResourceUpload({'id': id})
            assert resource_upload.storage_path, "no storage configured aborting"

            directory = resource_upload.get_directory(id)
            filepath = resource_upload.get_path(id)
            try:
                os.makedirs(directory)
            except OSError, e:
                ## errno 17 is file already exists
                if e.errno != 17:
                    raise

            with open(filepath, 'wb+') as out:
                for chunk in response.iter_content(1024):
                    if chunk:
                        out.write(chunk)

            Session.execute("update resource set url_type = 'upload', "
                            "url = '%s' where id = '%s'" % (filename, id))
            Session.execute("update resource_revision set url_type = 'upload', "
                            "url = '%s' where id = '%s' and "
                            "revision_id = '%s'" % (filename, id, revision_id))
            Session.commit()
            print "Saved url %s" % url
