import ckan.plugins as p
from ckan.model import Session
import ckan.lib.helpers as h
import json
import os

class FeatureSearchCommand(p.toolkit.CkanCommand):
    '''
    Usage:
        paster hdx-feature-search build
        - Writes a json file to be used to run custom searches of all
         Featured pages (Countries, Organizations, Topics, Crisis)
         We'll need to be changed in the event that we make crisis or
         Topics its own entity.
    '''
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def __init__(self, name):
        super(FeatureSearchCommand, self).__init__(name)

    def command(self):
        if not self.args or self.args[0] in ['-h', '--help', 'help'] or not len(self.args) in [1, 2]:
            print self.usage
            return

        cmd = self.args[0]
        self._load_config(load_site_user=False)
        if cmd == 'build':
            print 'Collecting Feature Pages...'
            self.buildIndex()
            print 'Index successfully built...'
        else:
            print 'Error: command "{0}" not recognized'.format(cmd)
            print self.usage

    def buildIndex(self):
        '''
        Grab all Organizations, Groups, and Vocabulary Topics and write a
        json file for lunr.js to search against
        '''
        index = list()
        groups = Session.execute('select id, title from "group"')
        for id, title in groups:
            url = h.url_for(controller='group',
                                    action='read',
                                    id=id,
                                    qualified=True)
            index.append({'title':title, 'url': url})

        topic = Session.execute("select id from vocabulary where name='Topics'")
        topic = [id for id in topic]
        topics = Session.execute("select id, name from tag where vocabulary_id='%s'" % (topic[0][0]))
        for id, name in topics:
            url = h.url_for(controller='tag',
                                    action='read',
                                    id=id,
                                    qualified=True)
            index.append({'title':name.capitalize(), 'url': url})

        dir_path = os.path.abspath('../ckanext-hdx_theme/ckanext/hdx_theme/public/scripts') 
        f = open(dir_path+'/feature-index.json', 'w')
        f.write(json.dumps(index))
