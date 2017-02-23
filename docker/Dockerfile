FROM teodorescuserban/hdx-ckan:latest

RUN rm -rf /srv/ckan && \
    mkdir /srv/ckan

COPY . /srv/ckan

RUN cd /srv/ckan && \
    pip install -r requirements.txt && \
    hdxckantool update && \
    hdxckantool plugins dev
