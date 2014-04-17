'''
Created on Apr 11, 2014

@author: alexandru-m-g
'''

import logging
import ckan.lib.navl.dictization_functions as df

from ckan.common import _

missing = df.missing
StopOnError = df.StopOnError
Invalid = df.Invalid


def groups_not_empty(key, data, errors, context):
    # All the extra logic here is needed to deal with the multi-step wizard used for creating a new dataset
    # We need to make sure that the validation only runs at the last step of the wizard
    allow_partial_update    = context.get('allow_partial_update',False)
    allow_state_change      = context.get('allow_state_change',False)
    groups_found            = False
    first_phase             = False
    
    for data_key, data_value in data.items():
        if data_key[0]=='__extras':
            wizard_phase    = data_value.get('_ckan_phase', 'Other')
            if wizard_phase == 'dataset_new_1':
                first_phase = True
                break
                
    if not first_phase and (allow_partial_update != allow_state_change) :
        for data_key, data_value in data.items():
            if data_key[0]=='groups' and data_key[2]=='id' and data_value != '-1':
                groups_found    = True
                break
        if not groups_found:
            errors[key].append(_('Missing value'))
            raise StopOnError
