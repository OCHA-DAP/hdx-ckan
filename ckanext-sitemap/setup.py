from setuptools import setup, find_packages
import sys
import os

version = '0.1'

setup(
        name='ckanext-sitemap',
        version=version,
        description="Sitemap extension for CKAN",
        long_description="""\
	""",
        classifiers=[
        ],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        keywords='',
        author='Aleksi Suomalainen',
        author_email='aleksi.suomalainen@nomovok.com',
        url='https://github.com/locusf/ckanext-sitemap',
        license='AGPL',
        packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
        namespace_packages=['ckanext', 'ckanext.sitemap'],
        include_package_data=True,
        zip_safe=False,
        install_requires=[
                # -*- Extra requirements: -*-
        ],
        setup_requires=[
                'nose'
        ],
        entry_points="""
        [ckan.plugins]
	# Add plugins here, eg
	sitemap=ckanext.sitemap.plugin:SitemapPlugin
	""",
)
