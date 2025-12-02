from setuptools import setup, find_packages

version = '0.1.0'

setup(
    name='ckanext-hdx_smtp_assumerole',
    version=version,
    description="CKAN plugin for AWS SES API with AssumeRole support",
    long_description='''
    This plugin enables CKAN to send emails via AWS SES API (not SMTP) using
    temporary credentials obtained through AWS STS AssumeRole. This is useful
    when running CKAN on EC2 instances with instance profiles.

    The plugin automatically:
    - Assumes an IAM role at startup
    - Uses SES API (boto3) instead of SMTP protocol
    - Supports temporary credentials with session tokens
    - Auto-refreshes credentials before expiry (no restart needed)
    - Supports HTML emails and file attachments

    Why SES API instead of SMTP?
    - SMTP only supports username/password authentication
    - Temporary credentials include session tokens that SMTP cannot use
    - SES API fully supports temporary credentials with session tokens

    Pattern: EC2 instance profile → AssumeRole → SES API (boto3)
    ''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
    ],
    keywords='ckan aws ses smtp assumerole iam security',
    author='HDX Team',
    author_email='hdx@un.org',
    url='https://github.com/OCHA-DAP/hdx-ckan',
    license='AGPLv3',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'boto3>=1.18.0',
        'botocore>=1.21.0',
    ],
    entry_points='''
        [ckan.plugins]
        hdx_smtp_assumerole=ckanext.hdx_smtp_assumerole.plugin:HDXSMTPAssumeRolePlugin
    ''',
)
