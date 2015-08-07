import ckan.plugins as p
from ckan.model import Session
import ckan.lib.helpers as h
import json
import os
from pylons import config

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
            buildIndex('../ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/search')
            print 'Index successfully built...'
        else:
            print 'Error: command "{0}" not recognized'.format(cmd)
            print self.usage

def buildIndex(path):
        '''
        Grab all Organizations, Groups, and Vocabulary Topics and write a
        json file for lunr.js to search against
        '''
        index = list()
        try:
            crises = config.get('hdx.crises').split(", ")
        except:
            crises = ['ebola', 'nepal-earthquake']
        groups = Session.execute('select name, title, is_organization from "group" where state=\'active\'')
        for name, title, is_org in groups:
            if is_org:
                page_type = 'organisation'
                url = h.url_for(controller='organization',
                                    action='read',
                                    id=name,
                                    qualified=True)
            else:
                if name in crises:
                    continue
                page_type = "location"
                

                url = h.url_for(controller='group',
                                    action='read',
                                    id=name,
                                    qualified=True)
            index.append({'title':title, 'url': url, 'type':page_type})

        ## I hate this, but given the way we did crisis
        ## I think this is the only way to go. Please update
        ## when new crisis are added

        index.append({'title':'Ebola', 'url':h.url_for(controller='ckanext.hdx_crisis.controllers.ebola_custom_location_controller:EbolaCustomLocationController',
            action='read',qualified=True), 'type':'crisis'})
        index.append({'title':'Nepal Earthquake', 'url':h.url_for(controller='ckanext.hdx_crisis.controllers.custom_location_controller:CustomLocationController',
                    action='read', id='nepal-earthquake', qualified=True), 'type':'crisis'})


        ## UNCOMMENT THIS TO ENABLE TOPIC PAGES AS WELL
        # topic = Session.execute("select id from vocabulary where name='Topics'")
        # topic = [id for id in topic]
        # topics = Session.execute("select id, name from tag where vocabulary_id='%s'" % (topic[0][0]))
        # for id, name in topics:
        #     url = h.url_for(controller='tag',
        #                             action='read',
        #                             id=id,
        #                             qualified=True)
        #     index.append({'title':name.capitalize(), 'url': url, 'type': 'topic'})

        dir_path = os.path.abspath(path)
        f = open(dir_path+'/feature-index.js', 'w')
        file_body = json.dumps(index)
        file_body = 'var feature_index='+file_body+';'
        f.write(file_body)
