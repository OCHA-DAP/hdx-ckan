'''
Created on September 25, 2015

@author: mbellotti
'''

import ckan.model as model

def hdx_dataset_purge(context, data_dict):
	'''
	Permenantly and completely delete a dataset from HDX
	'''
	dataset_ref = data_dict['id'] or data_dict['name']
	dataset = model.Package.get(unicode(dataset_ref))
	name = dataset.name
	rev = model.repo.new_revision()
	try:
		dataset.purge()
		model.repo.commit_and_remove()
		return True
	except:
		return False
        