FROM teodorescuserban/hdx-ckan:latest

RUN rm -rf /srv/ckan && \
    mkdir -p /srv/ckan

COPY . /srv/ckan/

RUN cd /srv/ckan && \
    pip install -r requirements.txt && \
    python setup.py develop && \
    hdxckantool update && \
    hdxckantool plugins dev

