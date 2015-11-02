# coding=UTF-8
# -*- coding: utf-8 -*-
import sys
import urllib

__author__ = 'dan'

import requests
import os

# url = 'http://localhost:5000/api/3/action/resource_create'
# api_key = '4a4ed4e3-571b-4b99-9bc1-ae1df26b77a8'
url = 'http://master.ckan.org/api/3/action/resource_create'
api_key = '27eb9769-eef3-4267-aaf1-be7038194732'

h_dict={'X-CKAN-API-Key': api_key}

data_dict = {}
data_dict['url_type'] = 'upload'
data_dict['resource_type'] = 'file.upload'
data_dict['package_id'] = 'asdgadsgadsgas'
data_dict['description'] = 'test desc'
data_dict['format'] = 'zip'
data_dict['name'] = u'Test_french_accents_éiés.zip'
data_dict['url'] = data_dict['name']
path = u'/Users/dan/hdx/scripts/db/Test_french_accents_éiés.zip'
resource_file = os.path.join(path)
files = {'upload': open(resource_file, 'rb')}

# files = [('upload', (u'Camps_Réfugiés_2.zip', open(resource_file, 'rb'), 'application/zip'))]
r = requests.post(url, data=data_dict, headers=h_dict, files=files, verify=False)

print "gata"
