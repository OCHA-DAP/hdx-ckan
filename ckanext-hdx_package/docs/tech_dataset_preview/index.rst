SETTING PREVIEW FOR A DATASET VIA API
=====================================

Field name: *dataset_preview* - stored at dataset level . Possible values:

first_resource - HDX will check resources from top to bottom (from position 0 to n) and will display the first resource which has a preview (e.g geopreview, quick charts)

no_preview - dataset will display no preview

resource_id - HDX will check which resource has the flag *dataset_preview_enabled* set to *True* and will display the preview of that resource. If the resource doesn't have a valid preview (geopreview, quick charts) then HDX will apply the *first_resource* strategy described above


SETTING PREVIEW FOR A RESOURCE VIA API
======================================

Field name: *dataset_preview_enabled* - stored at resource level. Possible values:

True - resource is set to display a preview on dataset page

False - resource is set not to display a preview on dataset page

Recommendation: when a resource field *dataset_preview_enabled* is set to *True* the other resources should have the field set to *False*. It is done automatically via UI, but when is done via API it is recommended to manually update and set the field for all resources.


IMPORTANT NOTE FOR UI USE
-------------------------

When UI is used to change the dataset preview, user has to edit the dataset and check/uncheck the dataset preview checkbox. When the checkbox is checked, a dropdown is displayed. The dropdown contains the first option: *First Resource* and the rest of the resources. User can select any resource to be displayed as default preview for dataset.

IMPORTANT NOTE FOR EXISTING DATASETS
------------------------------------

The existing datasets there are no values for *dataset_preview* or *dataset_preview_enabled* stored in database. HDX will consider by default that *dataset_preview* is set to *first_resource* and will display the first resource found with a preview (e.g. geopreview, quick charts)

