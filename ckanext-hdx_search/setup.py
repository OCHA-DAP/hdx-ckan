from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-hdx_search',
    version=version,
    description="specific search functions for HDX",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Marianne Bellotti',
    author_email='marianne.bellotti@gmail.com',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.hdx_search'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        hdx_search=ckanext.hdx_search.plugin:HDXSearchPlugin
    ''',
)
