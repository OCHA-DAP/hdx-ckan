ANALYTICS IN HDX
================

Useful information about HDX and Mixpanel
-----------------------------------------
There will be 3 mixpanel projects:

#. For the production server
#. For the testing/feature servers
#. For local servers running on dev's computers


Setup steps for sending events to the mixpanel servers
------------------------------------------------------

#. The **mixpanel token** needs to be setup in prod.ini under :code:`hdx.analytics.mixpanel.token`
#. The url to the enqueuing service needs to be setup in prod.ini as in :code:`hdx.analytics.enqueue_url = http://[gislayer_host]:[gislayer_port]/api/send-analytics`
#. The **gislayer** needs to be setup with the latest code. It's dependencies were updated as well ( *requirements.txt* )

   * | there is a new queue for processing analytics requests called **analytics_q**. So we need a rq worker listening on it.
       We can either use a separate worker for each queue or workers that listen on both queues.
   *  Information about how to run the **rqworker** can be found in
      `Running the redis queue worker for analytics <http://agartner.bitbucket.org/hdxjobprocessor/README.html#running-the-redis-queue-worker-for-analytics>`_


Setup steps for seeing mixpanel stats in HDX
--------------------------------------------

#. The latest `schema.xml <../../../ckanext-hdx_search/ckanext/hdx_search/hdx-solr/schema.xml>`_ needs to be used in solr
#. The **mixpanel secret** must be set in prod.ini under :code:`hdx.analytics.mixpanel.secret = OVERWRITE_WITH_SECRET_FROM_MP_PROJECT`
#. By default (as set in `common-config-ini.txt <../../../common-config-ini.txt>`_) the time for cache expiration is 1h.
   The setting responsible for this is :code:`hdx.analytics.hours_for_results_in_cache`. We should set this to **12** hours.
#. There is a new **paster** command that updates solr with the latest information from mixpanel. Please note that the
   information is actually taken from the same cache::

    /srv/ckan/ckanext-hdx_theme
    paster analytics-changes-reindex -c /srv/configs/prod.ini

   This should be run every **24** hours
