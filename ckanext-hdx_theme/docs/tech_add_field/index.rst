ADDING NEW DATASET FIELD (including indexing in solr)
=====================================================

Example fields: *has_quickcharts* - not stored but based on existing resource view of type *hdx_hxl_preview*

computed - steps marked with *computed* should be done for dataset properties that are computed (not stored in the db)

saved - steps marked with *saved* should be done for dataset properties that are stored in the db

indexed - steps marked with *indexed* should be done for dataset properties that are indexed in solr

filtering - steps marked with *filtering* should be done for dataset properties which will be used for filters


STEPS
-----

#. In `get.py <../../../ckanext-hdx_package/ckanext/hdx_package/actions/get.py>`_ at the end of *package_show* and/or
   *resource_show()* , Use the *_should_manually_load_property_value()* helped function to only inject the value in case
   the value is not already in the package_dict / resource_dict (loaded from solr).

   NOTE: can the (computed) property change without the dataset changing ? Then you probably need to trigger a dataset reindex
   after the property changes. For an example look here: the
   `resource_view_crreate() function <../../../ckanext-hdx_package/ckanext/hdx_package/actions/create.py>`_
   (computed, indexed)

#. In `search_controller.py <../../../ckanext-hdx_search/ckanext/hdx_search/controllers/search_controller.py>`_ (indexed, filtering)

   * for the system to identify the http request parameter as a filter it needs to realize this in the
     *_prepare_facets_info()* function. Either as part of the *checkboxes* list OR as part of the default facet titles
     which come from the *get_default_facet_titles()* function. NOTE that default facet
     titles can also be added via a plugin by implementing IFacets
   * also in *_prepare_facets_info()* function, manually extract the number of results for your checkbox facet
     (for checkbox facets). This number will be used in the UI

#. `In hdx_search module, in plugin.py <../../../ckanext-hdx_search/ckanext/hdx_search/plugin.py>`_ (indexed, filtering)

   * transform the HTTP request param (ext_quickcharts) into **fq** param for solr. In *before_search()*
   * add translation for the facet (how it should appear in UI). In *dataset_facets()*

#. In solr's `schema.xml <../../../ckanext-hdx_search/ckanext/hdx_search/hdx-solr/schema.xml>`_ (indexed) ::

   <field name="has_quickcharts" type="boolean" indexed="true" stored="true"/>

#. In the validation schemas - it should at least be part of the validation *show* schema for computed.
   Otherwise, for saved, properties it should be part of the *create* and *update* schemas as well.
   This is done in the `hdx_package module, in plugin.py <../../../ckanext-hdx_package/ckanext/hdx_package/plugin.py>`_
   (computed / saved)

#. For Mixpanel / Google Analytics to track filterting by this property.
   Change this in `google_analytics.js <../../../ckanext-hdx_theme/ckanext/hdx_theme/fanstatic/google-analytics.js>`_,
   in the *setUpSearchTracking()* function
   (indexed, filtering) 


IMPORTANT NOTE FOR SOLR INDEXED FIELDS
--------------------------------------

* the *schema.xml* file needs to end up in the solr container
* you might need a reindex to be able to filter by the new field

