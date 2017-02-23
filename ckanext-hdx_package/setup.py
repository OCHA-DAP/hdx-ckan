from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
    name='ckanext-hdx_package',
    version=version,
    description="Modifications to package (datasets) logic",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Marianne Bellotti',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.hdx_package'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        hdx_package=ckanext.hdx_package.plugin:HDXPackagePlugin
        hdx_analytics=ckanext.hdx_package.plugin:HDXAnalyticsPlugin
        hdx_chart_views=ckanext.hdx_package.plugin:HDXChartViewsPlugin
        hdx_geopreview_view=ckanext.hdx_package.plugin:HDXGeopreviewPlugin
        hdx_key_figures_view=ckanext.hdx_package.plugin:HDXKeyFiguresPlugin
        hdx_choropleth_map_view=ckanext.hdx_package.plugin:HDXChoroplethMapPlugin


        [paste.paster_command]
        hdx-migrate = ckanext.hdx_package.command:MigrateCommand
    ''',
)
