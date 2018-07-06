FROM unocha/alpine-solr:6.3.0-201701-01

COPY ckanext-hdx_search/ckanext/hdx_search/hdx-solr/schema.xml docker/solrconfig.xml docker/run_solr /srv/

RUN mv /srv/run_solr /etc/services.d/solr/run
