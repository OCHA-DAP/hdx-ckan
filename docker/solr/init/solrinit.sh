#!/bin/bash -e

cd /opt/solr

echo "waiting for zookeeper for a bit..."
sleep 10
echo "alright, uploading all configset..."
for c in $(ls /configsets/); do
    bin/solr zk upconfig -n $c -d /configsets/$c;
done
echo "done."
