from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-ungroups',
	version=version,
	description="Extended groups for the UN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Marianne Bellotti',
	author_email='marianne@exversion.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.ungroups'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=
	"""
        [ckan.plugins]
	ungroups=ckanext.ungroups.plugin:UNIGroupFormPlugin
	""",
)
