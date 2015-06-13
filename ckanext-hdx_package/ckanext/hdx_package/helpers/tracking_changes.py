'''
Created on Jan 19, 2015

@author:alexandru-m-g
'''

import logging
import sqlalchemy
import json
import ckan.model as model


log = logging.getLogger(__name__)

def add_tracking_summary_to_resource_dict(resource_dict):
    '''
    This function supplements _add_tracking_summary_to_resource_dict()
    from ckan/logic/action/get.py. It also checks to see if there is data
    for the new permalink.
    '''
    _erase_tracking_summary(resource_dict)
    existing_urls = _find_old_urls_for_resource(resource_dict['id'])
    unique_urls = set(existing_urls)

    for link in unique_urls:
        tracking_summary = model.TrackingSummary.get_for_resource(link)
        if tracking_summary:
            if 'tracking_summary' in resource_dict \
                    and resource_dict['tracking_summary']:
                summary = resource_dict['tracking_summary']
                summary['total'] = summary.get('total', 0) + tracking_summary.get('total', 0)
                summary['recent'] = summary.get('recent', 0) + tracking_summary.get('recent', 0)
            else:
                resource_dict['tracking_summary'] = tracking_summary

def _erase_tracking_summary(resource_dict):
    if 'tracking_summary' in resource_dict \
            and resource_dict['tracking_summary']:
        summary = resource_dict['tracking_summary']
        summary['total'] = 0
        summary['recent'] = 0

def _find_old_urls_for_resource(resource_id):
    q = sqlalchemy.text(
        "SELECT url, extras FROM resource_revision WHERE id='{}'".format(resource_id)
    )
    result = model.Session.connection().execute(q)

    if result and result.rowcount > 0:
        links = []
        extras_text_list = []
        for item in result:
            links.append(item[0])
            extras_text_list.append(item[1])

        perma_links = _extract_perma_links(extras_text_list)
        return links + perma_links
    else:
        return []

def _extract_perma_links(extras_text_list):

    response = []
    for jsonstring in extras_text_list:
        if jsonstring and 'perma_link' in jsonstring:
            try:
                json_dict = json.loads(jsonstring)
                perma_link = json_dict.get('perma_link', None)
                if perma_link:
                    response.append(perma_link)
            except:
                log.warn('problem parsing json string {}'.format(jsonstring))
    return response