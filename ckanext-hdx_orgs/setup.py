from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-hdx_orgs',
	version=version,
	description="adding extra fields to organization type",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Dan',
	author_email='danmihaila@gmail.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.hdx_orgs'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
	hdx_orgs=ckanext.hdx_orgs.plugin:HDXOrgFormPlugin
	""",
)

