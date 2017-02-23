.. You should enable this project on travis-ci.org and coveralls.io to make
   these badges work. The necessary Travis and Coverage config files have been
   generated for you.

.. image:: https://travis-ci.org/alexandru-m-g/ckanext-hdx_service_checker.svg?branch=master
    :target: https://travis-ci.org/alexandru-m-g/ckanext-hdx_service_checker

.. image:: https://coveralls.io/repos/alexandru-m-g/ckanext-hdx_service_checker/badge.png?branch=master
  :target: https://coveralls.io/r/alexandru-m-g/ckanext-hdx_service_checker?branch=master

.. image:: https://pypip.in/download/ckanext-hdx_service_checker/badge.svg
    :target: https://pypi.python.org/pypi//ckanext-hdx_service_checker/
    :alt: Downloads

.. image:: https://pypip.in/version/ckanext-hdx_service_checker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-hdx_service_checker/
    :alt: Latest Version

.. image:: https://pypip.in/py_versions/ckanext-hdx_service_checker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-hdx_service_checker/
    :alt: Supported Python versions

.. image:: https://pypip.in/status/ckanext-hdx_service_checker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-hdx_service_checker/
    :alt: Development Status

.. image:: https://pypip.in/license/ckanext-hdx_service_checker/badge.svg
    :target: https://pypi.python.org/pypi/ckanext-hdx_service_checker/
    :alt: License

=============
ckanext-hdx_service_checker
=============

.. Put a description of your extension here:
   What does it do? What features does it have?
   Consider including some screenshots or embedding a video!


------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-hdx_service_checker:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-hdx_service_checker Python package into your virtual environment::

     pip install ckanext-hdx_service_checker

3. Add ``hdx_service_checker`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

Document any optional config settings here. For example::

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.hdx_service_checker.some_setting = some_default_value


------------------------
Development Installation
------------------------

To install ckanext-hdx_service_checker for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/alexandru-m-g/ckanext-hdx_service_checker.git
    cd ckanext-hdx_service_checker
    python setup.py develop
    pip install -r dev-requirements.txt


-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.hdx_service_checker --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-hdx_service_checker on PyPI
---------------------------------

ckanext-hdx_service_checker should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-hdx_service_checker. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-hdx_service_checker
----------------------------------------

ckanext-hdx_service_checker is availabe on PyPI as https://pypi.python.org/pypi/ckanext-hdx_service_checker.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
