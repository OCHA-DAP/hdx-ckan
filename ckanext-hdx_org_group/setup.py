from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-hdx_org_group',
    version=version,
    description="Modifications to group and org logic",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Marianne Bellotti',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.hdx_org_group'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        hdx_org_group=ckanext.hdx_org_group.plugin:HDXOrgGroupPlugin
    ''',
)
