from setuptools import setup, find_packages

version = '0.1'

setup(
    name='ckanext-ytp-request',
    version=version,
    description="Member request for organizations",
    long_description="""\
    """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ytp', 'ckanext.ytp.request'],
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    message_extractors={
        'ckanext/ytp/request': [
            ('**.py', 'python', None),
            ('templates/**.html', 'ckan', None)
        ]
    },
    include_package_data=True,
    entry_points="""
        [ckan.plugins]
        ytp_request=ckanext.ytp.request.plugin:YtpRequestPlugin
    """,)
