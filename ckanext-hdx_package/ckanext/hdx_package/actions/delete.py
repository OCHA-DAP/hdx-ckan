'''
Created on September 25, 2015

@author: mbellotti
'''

import ckan.model as model
import ckan.logic

_check_access = ckan.logic.check_access
NotFound = ckan.logic.NotFound
_get_or_bust = ckan.logic.get_or_bust


def hdx_dataset_purge(context, data_dict):
    '''
    Permenantly and completely delete a dataset from HDX
    '''
    model = context['model']
    user = context['user']

    _check_access('package_delete', context, data_dict)

    dataset_ref = _get_or_bust(data_dict, 'id')
    dataset = model.Package.get(unicode(dataset_ref))
    if dataset is None:
        raise NotFound('Dataset "{id}" was not found.'.format(id=dataset_ref))

    name = dataset.name
    rev = model.repo.new_revision()
    try:
        dataset.purge()
        model.repo.commit_and_remove()
        return True
    except:
        return False
