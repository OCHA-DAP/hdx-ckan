'''
Created on Jan 19, 2015

@author:alexandru-m-g
'''

import ckan.model as model
import sqlalchemy

def add_tracking_summary_to_resource_dict(resource_dict):
    '''
    This function supplements _add_tracking_summary_to_resource_dict()
    from ckan/logic/action/get.py. It also checks to see if there is data
    for the new permalink.
    '''
    _erase_tracking_summary(resource_dict)
    existing_urls = _find_old_urls_for_resource(resource_dict['id'])
    perma_link = resource_dict.get('perma_link', None)
    if perma_link:
        existing_urls.append(perma_link)
    for link in set(existing_urls):
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
        "SELECT url FROM resource_revision WHERE id='{}'".format(resource_id)
    )
    result = model.Session.connection().execute(q)

    if result and result.rowcount > 0:
        return [item[0] for item in result]
    else:
        return []
