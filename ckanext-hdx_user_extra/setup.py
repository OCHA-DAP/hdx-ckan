from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='''ckanext-hdx_user_extra''',
    version='0.1',
    description="Creates user extra table",
    long_description='',
    url='',
    author='''Dan Mihaila''',
    author_email='''danmihaila@gmail.com''',
    # Choose your license
    license='',
    classifiers=[],
    keywords='''CKAN user extra''',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[],
    include_package_data=True,
    package_data={},
    data_files=[],
    entry_points='''
        [ckan.plugins]
        hdx_user_extra=ckanext.hdx_user_extra.plugin:HDX_User_ExtraPlugin

        [paste.paster_command]
        hdx_user_extra = ckanext.hdx_user_extra.command:InitDBCommand
    ''',
)
