DOWNLOAD FILES/RESOURCES FROM HDX
================

There are several ways to download the files/resources from HDX.

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

