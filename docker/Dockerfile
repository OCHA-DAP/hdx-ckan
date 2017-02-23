FROM teodorescuserban/hdx-ckan:latest

RUN rm -rf /srv/ckan && \
    mkdir -p /srv/ckan

COPY . /srv/ckan/

RUN ls -l /srv/ckan && \
    pip install -r requirements.txt && \
    hdxckantool update && \
    hdxckantool plugins dev
