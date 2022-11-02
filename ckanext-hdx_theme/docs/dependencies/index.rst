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
* IMPORTANT ! The owner of the project folder needs to be the same as the user that runs the *pip-compile* and
  *pip-sync* commands. Otherwise you can get *RemoteNotFoundError* errors when pip tries to use vcs (git).


Compilation steps
-----------------

#. Make sure to have *pip-tools* installed, at least version 5.5.0 for python2 and 6.6.0 for python3:
    *  FOR PYTHON 2::

        pip install pip-tools==5.5.0

    *  FOR PYTHON 3::

        pip install pip-tools==6.6.0

#. Compile the main dependencies:

   *  FOR PYTHON 2::

       pip-compile requirements-py2.in --output-file=requirements-py2.txt

   *  FOR PYTHON 3::

       pip-compile requirements.in --output-file=requirements.txt

#. Compile the dev dependencies:

   *  FOR PYTHON 2::

       pip-compile dev-requirements-py2.in --output-file=dev-requirements-py2.txt

   *  FOR PYTHON 3::

       pip-compile dev-requirements.in --output-file=dev-requirements.txt

#. Make sure your python environment has the correct libraries installed. Notice that
   we're using the *dev-requirements-local.txt* file here:

   *  FOR PYTHON 2::

       pip-sync requirements-py2.txt dev-requirements-py2.txt

   *  FOR PYTHON 3::

       pip-sync requirements.txt dev-requirements.txt
