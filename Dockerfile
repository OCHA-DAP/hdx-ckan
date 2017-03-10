FROM teodorescuserban/hdx-ckan:latest

RUN rm -rf /srv/ckan && \
    mkdir -p /srv/ckan

COPY . /srv/ckan/

RUN ls -l /srv/ckan && \
    easy_install pip==9.0.1 && \
    apt-get update && apt-get install -y libffi-dev libssl-dev && \
    rm -rf /usr/local/man && \
    pip install --upgrade  -r /srv/ckan/requirements.txt && \
    hdxckantool update && \
    hdxckantool plugins dev
