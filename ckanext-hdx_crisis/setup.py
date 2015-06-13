from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-hdx_crisis',
    version=version,
    description="Module for hdx crisis pages",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='alexandru-m-g',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.hdx_crisis'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        hdx_crisis=ckanext.hdx_crisis.plugin:HDXCrisisPlugin
    ''',
)
