USING THE API TO SEARCH ON HDX
==============================

The main API endpoint for searching and faceting on HDX is: :code:`/api/3/action/package_search`.

TL;DR
-----
If you just want to quickly start querying:

#. Take the example from "POST Query Example" section and parameterize it as explained below
#. For filter queries, like filtering by location or organization add items to the *fq_list* like:

   :code:`"{!tag=TAG_NAME}FIELD:\"VALUE1\" or \"VALUE2\""`

   For example: :code:`{!tag=groups}groups:\"rou\" OR groups:\"alb\"`
#. For text queries fill the *q* field like: :code:`"q": "SEARCH TERMS"`. If there's no text query you can just send
   an empty field :code:`"q": ""`
#. Of course, you can combine 2 and 3
#. Also, take a look at possible values for the "sort" query field

HTTP Verbs
----------

The allowed verbs for accessing it are *GET* and *POST*. The way in which the 2 verbs are used is very similar.
The parameters that you would pass in the URL of a GET request you can pass in the JSON object in the body of a POST
request.

For example a URL parameter like :code:`&q=health` would look like::

  {
    ...
    "q": "health"
    ...
  }

Since it's easier to read and also easier to use I'll assume for the rest of this document that we're using a POST HTTP request.

POST Query Example
------------------

Below you can see a simple example that queries for the "health" term and filters by the location "rou" (Romania)
and organizations "world-bank-group" (World Bank Group ) or world-health-organization (World Health Organization).

.. code-block:: json

  {
    "q": "health",
    "fq": "+dataset_type:dataset -extras_archived:true",
    "fq_list": [
      "{!tag=groups}groups:\"rou\"",
      "{!tag=organization}organization:\"world-bank-group\" OR organization:\"world-health-organization\""
    ],
    "facet.field": [
      "{!ex=groups}groups",
      "{!ex=res_format}res_format",
      "{!ex=organization}organization",
      "{!ex=vocab_Topics}vocab_Topics",
      "{!ex=license_id}license_id"
    ],
    "facet.limit": 200,
    "sort": "score desc, if(gt(last_modified,review_date),last_modified,review_date) desc",
    "start": 0,
    "rows": 25
  }

Query Fields
------------

*  **q** - This is generally used for normal text queries. In the case of the example above the value of this field is
   "health". For more information see `INFORMATION ABOUT THE SEARCH ENGINE IN HDX <index.rst>`_
*  **fq** - This is the filter query. Generally, filters that are always applies for your type of search should be
   placed here. :code:`+dataset_type:dataset` means we're only interested in "normal" datasets. There are other types
   of datasets in HDX (like *showcases*). :code:`-extras_archived:true` means we want to remove archived datasets
   from the search results
*  **fq_list** - This is very similar to *fq*, it's also a filter query but allows us to pass a list of filter queries.
   Here we usually pass the filters applied by the user in the browser. A few notes:

   *  inside a filter category we're using **OR** between the filter values. For example, if we would want to filter
      by "Romania" and "Albania" (in other words, if we were looking for datasets that are in either "Romania" or "Albania")
      then the a *fq_list* item would look like :code:`{!tag=groups}groups:\"rou\" OR groups:\"alb\"`
   *  each item in the list can have a **tag** (as can be seen in the example above), which identifies the filter query.
      This *tag* is used when creating the facets (the :code:`{!ex=TAG_NAME}` in the *facet.field* items) in order to
      tell the search engine to NOT take into consideration that specific filter query when computing the numbers for that facet.
      In other words, because we use an **OR** filter inside a filter category, when filtering by location "Romania"
      we don't want the "Location" facet to be filtered by "Romania".
      In our example, we want to know how many datasets there are for "Albania" disregarding the current "Romania" filter query.
*  **facet.fields** - This list represents the list of facets (filter categories) for which the search engine should
   compute faceting numbers (the numbers that appear next to each filter value in the UI). The default facets
   (shown in the example above) are:

   *  Locations - field name *groups*
   *  Organizations - field name *organization*
   *  Resource formats - field name *res_format*
   *  Tags - field name *vocab_Topics*
   *  Licenses - field name *license_id*

   Please note, that because we're using **OR** between filter values, each of the items above starts with
   :code:`{!ex=TAG_NAME}`. The *TAG_NAME* is the same value used in the *fq_list* items in
   :code:`{!tag=TAG_NAME}` and its meaning is that the respective filter query shouldn't influence the numbers
   of the current facet item.
*  **facet.limit** - Represents the maximum number of values that should appear in a filter category
*  **sort** - The dataset field or expression based on which the dataset results should be sorted.

   **When there's no text query** (empty *q* field) present the datasets should be sorted in descending order by the time
   when they were last modified. However we're only interested in significant updates to the datasets and
   there are 2 dates in HDX datasets that represent a significant change:

   *  *last_modified* - the date when the data inside a dataset was last modified
   *  *review_date* - the date when a person looked at the data in a dataset and decided that even if it was not
      modified lately it's still up to date.

   In conclusion we want to sort in descending order by the maximum of these 2 dates so we use the following expression:
   :code:`if(gt(last_modified,review_date),last_modified,review_date) desc`

   If **there is a text query** (like in the example above ::code::`q=health`) then the default sorting order is by
   how *relevant* the dataset is to the search query. The search engine assigns a score to each dataset in the result
   list and that score should be used:
   :code:`score desc, if(gt(last_modified,review_date),last_modified,review_date) desc`
   This means sort by score in descending order and if some datasets have the same score sort them by when they were
   last modified.

   Other sorting fields that could be used:

   *  :code:`metadata_created desc` - sort descending by the time when the datasets were created
   *  :code:`title_case_insensitive asc` - sort ascending by the title of the dataset
   *  :code:`pageviews_last_14_days desc` - sort descending by the number of page views that the dataset had in the
      last 14 days. It's what we call "Trending"
   *  :code:`total_res_downloads desc` - sort descending by the total number of resource downloads of the dataset
*  **start** - This is used for pagination. It's the index of the first item that should be shown in the results.
   For the first page this is 0.
*  **rows** - This is used for pagination. It's the number of datasets that should be shown on a page.


Query results
-------------
The result of the query is a JSON object. Most importantly, this object has a "success" field which should be *true*.
If that's the case, then the actual data is the object in the "result" field. The important fields of this object are:

*  **count** - The total number of results of the query
*  **results** - This contains the actual list of datasets. Each item contains all the fields of a dataset.
   Please note that because of pagination, the number of item in the list can be lower than the *count* value
*  **search_facets** - This object contains a field for each facet (filter category) that we supplied in *facet.field*.
   Inside it, the **items** field  contains the filter category values with the:

   *  *count* - number of datasets for this value
   *  *name* - the identifier of the entity by which we filtered (ex: "rou" for location Romania).
      This value should be used when filtering by this filter category value
   *  *display_name* - the string that should be displayed in the UI (ex: "Romania")

Example::

  {
      "success": true,
      "result": {
          "count": 12,
          ....
          "results": [
              {
                  "id": "b1dc6d30-65bb-4a69-bd61-14733536a350",
                  "name": "world-bank-health-indicators-for-romania",
                  "title": "Romania - Health",
                  "resources": [....],
                  "tags": [....],
                  "notes": "Contains data from the World Bank ....",
                  ....
              }
          ],
          "search_facets": {
             "organization": {
                  "title": "organization",
                  "items": [
                      {
                          "name": "world-health-organization",
                          "display_name": "World Health Organization",
                          "count": 1
                      },
                      ....
                  ]
             },
             "vocab_Topics": {
                  "title": "vocab_Topics",
                  "items": [
                      {
                          "name": "youth",
                          "display_name": "youth",
                          "count": 1
                      },
                      ....
             },
             ....
          }
  }


Featured Filters
----------------
The featured filters are built in different ways:

*  some of them are simple facet fields (facet.field). These facets are based on a dataset property.
*  while others are built on facet queries (facet.query). These generally check which datasets have a certain tag.

Below is a list of the featured filters:

Sub-national (facet.field)
__________________________

**Facet**::

  {
    "facet.field": [
      ...
      "subnational",
      ...
    ],
  }
In the response we're interested in the facet item with the *name* "true".

**Filter** - when filtering a new field should be set in the query :code:`ext_subnational` with value 1::

  {
    "q": ....,
    "fq": ....,
    "ext_subnational": 1
  }


Geodata (facet.field)
_____________________

**Facet**::

  {
    "facet.field": [
      ...
      "has_geodata",
      ...
    ],
  }

In the response we're interested in the facet item with the *name* "true".

**Filter** - when filtering a new field should be set in the query :code:`ext_geodata` with value 1::

  {
    "q": ....,
    "fq": ....,
    "ext_geodata": 1
  }


Datasets on request (facet.field)
_________________________________

**Facet**::

  {
    "facet.field": [
      ...
      "extras_is_requestdata_type",
      ...
    ],
  }

**NOTE:** Because this field is of type text one of the facet items names will be "fals" instead of "false".
In the response we're anyway only interested in the facet item with the *name* "true".

**Filter** - when filtering a new field should be set in the query :code:`ext_requestdata` with value 1::

  {
    "q": ....,
    "fq": ....,
    "ext_requestdata": 1
  }


Datasets with Quick Charts (facet.field)
________________________________________

**Facet**::

  {
    "facet.field": [
      ...
      "has_quickcharts",
      ...
    ],
  }


In the response we're interested in the facet item with the *name* "true".

**Filter** - when filtering  a new field should be set in the query :code:`ext_quickcharts`::

  {
    "q": ....,
    "fq": ....,
    "ext_quickcharts": 1
  }

Datasets with Showcases (facet.field)
_____________________________________

**Facet**::

  {
    "facet.field": [
      ...
      "has_showcases",
      ...
    ],
  }

In the response we're interested in the facet item with the *name* "true".

**Filter** - when filtering a new field should be set in the query :code:`ext_showcases` with value 1::

  {
    "q": ....,
    "fq": ....,
    "ext_showcases": 1
  }


Administrative Divisions (facet.query)
______________________________________
In this case we're NOT building the facet as before ( this facet is not based on a property of the dataset). The
actual logic here is: does the dataset have the *"administrative divisions" tag* ?
For this we use the :code:`facet.query` field in the query.

**Facet**::

  {
    "facet.field": ...,
    "facet.query": [
      "{!key=administrative_divisions} vocab_Topics:\"administrative divisions\""
    ],
  }

In this case, because we have used the key _administrative_divisions_ the response will contain an item with
the *name* "administrative_divisions" in the :code:`$.result.search_facets.queries` list. Example::

  {
    "success": true,
    "result": {
        "count": 12,
        ....
        "results": [...],
        "search_facets": {
          "organization": {...},
          "vocab_Topics": {...},
          ....
          "queries": [
            {
              "count": 2,
              "name": "administrative_divisions",
              "display_name": "administrative_divisions"
            }
          ],
        }
  }

**Filter** - when filtering a new field should be set in the query :code:`ext_administrative_divisions` with value 1::

  {
    "q": ....
    "fq": ....
    "ext_administrative_divisions": 1
  }


Datasets with HXL tags (facet.query)
_____________________________________
(please check the section about the `Administrative Divisions (facet.query)`_ featured filter for more information on
facet queries - :code:`facet.query`.
That section also contains an example on how to find the facet items in the response.)

**Facet**::

  {
    "facet.field": ...,
    "facet.query": [
      "{!key=hxl} vocab_Topics:hxl"
    ],
  }


**Filter** - when filtering a new field should be set in the query :code:`ext_hxl` with value 1::

  {
    "q": ....
    "fq": ....
    "ext_hxl": 1
  }


Datasets with SADD tags (facet.query)
_____________________________________
(please check the section about the `Administrative Divisions (facet.query)`_ featured filter for more information on
facet queries - :code:`facet.query`.
That section also contains an example on how to find the facet items in the response.)

**Facet**::

  {
    "facet.field": ...,
    "facet.query": [
      "{!key=sadd} vocab_Topics:\"sex and age disaggregated data - sadd\""
    ],
  }


**Filter** - when filtering a new field should be set in the query :code:`ext_sadd` with value 1::

  {
    "q": ....
    "fq": ....
    "ext_sadd": 1
  }

CODs (facet.query)
_____________________________________
(please check the section about the `Administrative Divisions (facet.query)`_ featured filter for more information on
facet queries - :code:`facet.query`.
That section also contains an example on how to find the facet items in the response.)

**Facet**::

  {
    "facet.field": ...,
    "facet.query": [
      "{!key=cod} vocab_Topics:\"common operational dataset - cod\""
    ],
  }


**Filter** - when filtering a new field should be set in the query :code:`ext_cod` with value 1::

  {
    "q": ....
    "fq": ....
    "ext_cod": 1
  }
