import ckan.plugins as p
import ckanext.hdx_pages.model as pages_model


class InitDBCommand(p.toolkit.CkanCommand):
    '''
    Usage:
        paster hdx_pages [initdb]
        Creates the table in db
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(InitDBCommand, self).__init__(name)

    def command(self):
        if not self.args or self.args[0] in ['-h', '--help', 'help'] or not len(self.args) in [1, 2]:
            print self.usage
            return

        cmd = self.args[0]

        self._load_config(load_site_user=False)
        if cmd == 'initdb':
            print 'Creating table for pages.'
            self.initdb()
            print 'Finished'
        elif cmd == 'cleandb':
            print 'Cleaning table of pages.'
            self.cleandb()
            print 'Finished'
        elif cmd == 'patchdb':
            print 'Patching table of pages and adding column '
            self.patchdb(self.args[1])
            print 'Finished'
        else:
            print 'Wrong argument, see usage:'
            print self.usage

    def initdb(self):
        pages_model.create_table()

    def cleandb(self):
        pages_model.delete_table()

    def patchdb(self):
        pages_model.patch_table()
