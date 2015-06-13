from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-hdx_theme',
	version=version,
	description="Theme for HDX installations of CKAN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Marianne Bellotti',
	author_email='marianne.bellotti@gmail.com',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.hdx_theme'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=
	"""
        [ckan.plugins]
	hdx_theme=ckanext.hdx_theme.plugin:HDXThemePlugin
	[paste.paster_command]
    custom-less-compile = ckanext.hdx_theme.cli.cli:CustomLessCompile
	""",
)
