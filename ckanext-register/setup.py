from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-register',
	version=version,
	description="Disable user registration",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Arti',
	author_email='aalecs@gmail.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.register'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
        register=ckanext.register.plugin:DisableUserRegistration
	""",
)
