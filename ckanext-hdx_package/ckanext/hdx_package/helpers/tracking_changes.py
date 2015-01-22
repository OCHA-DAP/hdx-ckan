'''
Created on Jan 19, 2015

@author:alexandru-m-g
'''

import ckan.model as model

def add_tracking_summary_to_resource_dict(resource_dict):
    '''
    This function supplements _add_tracking_summary_to_resource_dict()
    from ckan/logic/action/get.py. It also checks to see if there is data
    for the new permalink.
    '''
    url = resource_dict.get('perma_link', None)
    if url:
        tracking_summary = model.TrackingSummary.get_for_resource(url)
        if tracking_summary:
            if 'tracking_summary' in resource_dict \
                    and resource_dict['tracking_summary']:
                summary = resource_dict['tracking_summary']
                summary['total'] = summary.get('total', 0) + tracking_summary.get('total', 0)
                summary['recent'] = summary.get('recent', 0) + tracking_summary.get('recent', 0)
            else:
                resource_dict['tracking_summary'] = tracking_summary
