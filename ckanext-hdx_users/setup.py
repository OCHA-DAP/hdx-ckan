from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-hdx_users',
    version=version,
    description="An extension modifying things affecting users",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Marianne Bellotti',
    author_email='marianne.bellotti@gmail.com',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.hdx_users'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        hdx_mail_validate=ckanext.hdx_users.plugin:HDXValidatePlugin
        hdx_users=ckanext.hdx_users.plugin:HDXUsersPlugin

        [paste.paster_command]
        user_validation = ckanext.hdx_users.command:ValidationCommand
    ''',
)
