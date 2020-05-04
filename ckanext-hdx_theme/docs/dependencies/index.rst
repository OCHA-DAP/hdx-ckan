Compiling the dependencies
==========================

We're using `pip-tools <https://github.com/jazzband/pip-tools>`_ to manage our dependencies.

Notes
-----
* So the main dependencies are in *requirements.in*
* The dev dependencies are in *dev-requirements.in* .
  Please note that this file starts with :code:`-c requirements.txt`
  This tells *pip-compile* to take into consideration the requirements from that file
  when compiling the dev dependencies
* There's a conflict that can't be solved between `mailchimp <https://pypi.org/project/mailchimp/>`_
  (from *requirements.in*) and *coveralls* from
  *dev-requirements.in*: they need different versions of the same package *docopt*.

  * So we will create **2** dev requirements files:

    * *dev-requirements.txt* will be used by Travis
    * *dev-requirements-local.txt* will be used for local development
  * That's why we need to manually
    add *coveralls* **manually** at the end of *dev-requirements.txt* after compilation.
  * Maybe we could switch to using
    `another mailchimp library <https://pypi.org/project/mailchimp3/>`_ in the near future

Compilation steps
-----------------

#. Make sure to have *pip-tools* installed, at least version 5.0.0::

    pip install pip-tools==5.0.0

#. Compile the main dependencies::

    pip-compile requirements.in --output-file=requirements.txt

#. Compile the dev dependencies::

    pip-compile dev-requirements.in --output-file=dev-requirements.txt
    cp dev-requirements.txt dev-requirements-local.txt

#. Add *coveralls* manually to *dev-requirements.txt*::

    ....
    xmltodict==0.12.0         # via moto
    zipp==1.2.0               # via importlib-metadata
    coveralls

#. Make sure your python environment has the correct libraries installed. Notice that
   we're using the *dev-requirements-local.txt* file here::

    pip-sync requirements.txt dev-requirements-local.txt
