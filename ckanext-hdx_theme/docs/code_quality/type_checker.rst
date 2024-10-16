Code Quality
============

Type Checker Configuration
++++++++++++++++++++++++++
This section details enabling and configuring type checking within PyCharm.

Enabling Type Checking in PyCharm
---------------------------------

1. Go to `File` > `Settings` (or `Preferences` on macOS) > `Editor` > `Inspections`.
2. Enable the following inspections:

   * Python > ``Incorrect type``
   * Python > ``Missing type hinting for function definition``

3. For the ``Missing type hinting for function definition`` inspection, click on it and uncheck the ``Only when types are known`` option.

Optional Configuration
----------------------

1. You can adjust the severity level to ``Warning`` or ``Error`` for both inspections by clicking on them and selecting the desired level under the ``Severity`` option.

Manually Running Type Checking Inspections
------------------------------------------

1. Go to `Code` > `Inspect Code`.
2. Choose the scope (e.g., `Current File` or `Whole Project`).

Running Pyright in the CKAN Container
-----------------------------------------------------------
To run Pyright manually within the CKAN Docker container, follow these steps:

1. Install Node.js and npm on the CKAN Docker container:

::

       # Enter the CKAN Docker container
       docker-compose exec -it ckan /bin/bash

       # Install Node
       curl -sL https://deb.nodesource.com/setup_22.x | bash -
       apt-get install -y nodejs

2. Install Pyright globally using ``npm``:

::

       npm install -g pyright

3. To run Pyright within the CKAN Docker container, execute the following command:

::

       docker-compose exec -T ckan pyright /srv/ckan/<path>
