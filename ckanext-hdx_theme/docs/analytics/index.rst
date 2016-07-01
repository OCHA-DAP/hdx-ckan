ANALYTICS IN HDX
================

Useful information about HDX and Mixpanel
-----------------------------------------
There will be 3 mixpanel projects:

#. For the production server
#. For the testing/feature servers
#. For local servers running on dev's computers


Setup steps
-----------

#. The **mixpanel token** needs to be setup in prod.ini under :code:`hdx.analytics.mixpanel.token`
#. The **gislayer** needs to be setup with the latest code. It's dependencies were updated as well ( *requirements.txt* )

   * | there is a new queue for processing analytics requests called **analytics_q**. So we need a rq worker listening on it.
       We can either use a separate worker for each queue or workers that listen on both queues.
   *  Information about how to run the **rqworker** can be found in
      `Running the redis queue worker for analytics <http://agartner.bitbucket.org/hdxjobprocessor/README.html#running-the-redis-queue-worker-for-analytics>`_
