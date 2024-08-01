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
