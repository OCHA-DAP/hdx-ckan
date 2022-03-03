import click
import logging

import json
import os

import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
from ckan.model import Session

config = tk.config

log = logging.getLogger(__name__)


@click.command(short_help='Compile all custom less themes')
def hdx_feature_search():
    '''
    Usage:
        paster hdx-feature-search build   or use   hdxckantool feature
        - Writes a json file to be used to run custom searches of all
         Featured pages (Countries, Organizations, Topics, Crisis)
         We'll need to be changed in the event that we make crisis or
         Topics its own entity.
    '''
    log.info('Collecting Feature Pages...')
    _buildIndex(config.get('hdx.lunr.index_location'))
    log.info('Index successfully built...')



def _buildIndex(path):
    '''
    Grab all Organizations, Groups, and Vocabulary Topics and write a
    json file for lunr.js to search against
    '''
    index = list()
    try:
        crises = config.get('hdx.crises').split(", ")
    except:
        crises = ['ebola', 'nepal-earthquake']
    query = '''
    select g.name, g.title, g.is_organization, upper(coalesce(ge.value, g.name)) as code
    from "group" g LEFT OUTER JOIN group_extra ge ON g.id = ge.group_id and ge.key='org_acronym' and ge.state='active'
    where g.state='active'
    '''
    groups = Session.execute(query)
    for name, title, is_org, code in groups:
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

        if code and code != "":
            index.append({'title': u'{} ({})'.format(title, code), 'url': url, 'type': page_type})
        else:
            index.append({'title': u'{}'.format(title), 'url': url, 'type': page_type})

    ## I hate this, but given the way we did crisis
    ## I think this is the only way to go. Please update
    ## when new crisis are added

    index.append({'title': 'West Africa Ebola Outbreak 2014', 'url': h.url_for(
        'hdx_ebola.read', qualified=True), 'type': 'event'})
    index.append({'title': 'Nepal Earthquake', 'url': h.url_for(
        controller='ckanext.hdx_crisis.controllers.custom_location_controller:CustomLocationController',
        action='read', id='nepal-earthquake', qualified=True), 'type': 'event'})

    # pages

    # index.append({'title': 'El Nino',
    #               'url': h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
    #                                action='read_event', id='elnino', qualified=True), 'type': 'event'})
    # index.append({'title': 'Lake Chad',
    #               'url': h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
    #                                action='read_event', id='lake-chad', qualified=True), 'type': 'event'})
    # index.append({'title': 'Rohingya Displacement',
    #               'url': h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
    #                                action='read_event', id='rohingya-displacement', qualified=True), 'type': 'event'})
    # index.append({'title': 'Common Operational Dataset (COD)',
    #               'url': h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
    #                                action='read_dashboards', id='cod', qualified=True), 'type': 'topic'})
    # index.append({'title': 'Protection of Civilians (PoC)',
    #               'url': h.url_for(controller='ckanext.hdx_pages.controllers.custom_page:PagesController',
    #                                action='read_dashboards', id='poc', qualified=True), 'type': 'topic'})
    pages = Session.execute("select name, title, type, description from page where state='active'")
    for name, title, _type, description in pages:
        action = 'hdx_event.read_event' if _type == 'event' else 'hdx_dashboard.read_dashboard'
        index.append({'title': title or name,
                      'extra_terms': description,
                      'url': h.url_for(action, id=name, qualified=True),
                      'type': 'event'})

    # visualizations

    index.append({'title': 'Missing Migrants',
                  'url': '//data.humdata.org/visualization/missing-migrants/ ', 'type': 'visualization'})
    index.append({'title': 'Lake Chad Crisis Dashboard',
                  'url': '//data.humdata.org/visualization/ocha-lake-chad/ ', 'type': 'visualization'})
    index.append({'title': 'Nepal: Community Perceptions Survey',
                  'url': '//ocha-dap.github.io/hdxviz-nepal-community-survey/ ', 'type': 'visualization'})
    index.append({'title': 'Somalia Humanitarian Dashboard',
                  'url': '//data.humdata.org/visualization/somalia-monitoring/ ', 'type': 'visualization'})
    index.append({'title': 'Somalia Cash 3w',
                  'url': 'https://data.humdata.org/visualization/somalia-cash-programing-v3/ ', 'type': 'visualization'})
    index.append({'title': 'A journey of 1000 kilometers',
                  'url': 'https://data.humdata.org/visualization/a-journey-of-1000km/ ', 'type': 'visualization'})
    # index.append({'title': 'Chattam House Refugee Data',
    #               'url': '//baripembo.github.io/chathamhouse-refugeedata/ ', 'type': 'visualization'})
    # index.append({'title': 'Education Above All 3W',
    #               'url': '//ndongamadu.github.io/hdx-3w-education-above-all/ ', 'type': 'visualization'})

    # HDX-6332
    # index.append({'title': 'South Sudan Map Explorer',
    #               'url': '//data.humdata.org/mpx/#/name/south-sudan/ ', 'type': 'visualization'})
    # index.append({'title': 'Lake Chad Map Explorer',
    #               'url': '//data.humdata.org/mpx/#/name/lake-chad ', 'type': 'visualization'})

    index.append({'title': 'WFP Food Market Prices',
                  'url': '//data.humdata.org/visualization/wfp-food-price/', 'type': 'visualization'})

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
    f = open(dir_path + '/lunr/feature-index.js', 'w')
    file_body = json.dumps(index)
    file_body = 'var feature_index=' + file_body + ';'
    f.write(file_body)
