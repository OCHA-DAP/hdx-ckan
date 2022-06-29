HDX DOCUMENTATION
=================

PYTHON DEPENDENCY MANAGEMENT
++++++++++++++++++++++++++++
Information about compiling (dev-)requirements.txt can be found here `Dependency Management <dependencies/index.rst>`_


ANALYTICS
+++++++++
Information about how we collect and use analytics information can be found here `Analytics Documentation <analytics/index.rst>`_


SEARCH ENGINE
+++++++++++++
Information about how the CKAN search results are being computed can be found here `Search Documentation <search/index.rst>`_

Information about how to use the API endpoint :code:`package_search()` can be found here `Using the API to Search on HDX <search/package_search.rst>`_


DATASET FIELDS
++++++++++++++

SPECIAL FIELDS
--------------
Information about the fields and the dataset creation form can be found here `Special Dataset Fields <special_fields/index.rst>`_


HOW TO ADD A NEW FIELD
----------------------
Adding a new field to dataset. Please note that doesn't necessarily mean storing a new field. It might be a computed field also:
`Adding a new field to datasets <tech_add_field/index.rst>`_

DOWNLOAD RESOURCES
--------------
Resources can be downloaded using the following urls:

- if resource is uploaded in HDX and specifying filename:
  
  - :code:`/dataset/<dataset_id>/resource/<resource_id>/download/<filename>`

- if resource is uploaded in HDX and NOT specifying filename:
  
  - :code:`/dataset/<dataset_id>/resource/<resource_id>/download/`

- by specifying the position of the resource (starting with index 0):
  
  - :code:`/dataset/<dataset_id>/resource_at_position/<position>/download/`

- getting the first resource in the dataset:
  
  - :code:`/dataset/<dataset_id>/resource_first/download/`
