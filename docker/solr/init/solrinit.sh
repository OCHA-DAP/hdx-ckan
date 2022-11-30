#!/bin/bash -e

cd /opt/solr

echo "waiting for zookeeper for a bit..."
sleep 10
echo "alright, uploading hdx-search configset..."
bin/solr zk upconfig -n hdx-solr -d /configsets/hdx-solr;
echo "done."
