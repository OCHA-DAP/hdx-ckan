from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-metadata_fields',
	version=version,
	description="HDX CKAN metadata fields",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='alexandru-m-g',
	author_email='alexandru-m-g@users.noreply.github.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.metadata_fields'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
        metadata_fields=ckanext.metadata_fields.plugin:HdxMetadataFieldsPlugin
        dataset_auth=ckanext.metadata_fields.dataset_auth:DatasetIAuthFunctionsPlugin  
	# Add plugins here, eg
	# myplugin=ckanext.metadata_fields:PluginClass
	""",
)
