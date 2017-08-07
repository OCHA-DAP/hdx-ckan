FROM unocha/hdx-base-ckan:latest

ENV HDX_CKAN_WORKERS=4 \
    INI_FILE=/etc/ckan/prod.ini

COPY . /srv/ckan/

WORKDIR /srv/ckan

# /srv/pgb /etc/service/pgb && \
    
RUN rm -rf /usr/local/man && \
    mkdir -p /var/log/ckan /srv/filestore /etc/service/ckan /etc/ckan && \
    cp -a docker/prod.ini.tpl /etc/ckan && \
    cp -a docker/run_ckan /etc/service/ckan/run && \
    chmod +x /etc/service/ckan/run && \
    chown www-data:www-data -R /var/log/ckan /srv/filestore && \
    curl -s -o /srv/hdxckantool.py https://raw.githubusercontent.com/OCHA-DAP/hdx-infra-tools/master/hdxckantool.py && \
    chmod +x /srv/hdxckantool.py && \
    ln -s /srv/hdxckantool.py /usr/sbin/hdxckantool && \
    echo "application/vnd.geo+json       geojson" >> /etc/mime.types && \
    easy_install pip==9.0.1 && \
    pip install --upgrade --no-cache-dir setuptools && \
    python setup.py develop && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir newrelic && \
    hdxckantool plugins dev && \
    newrelic-admin generate-config LICENSE_KEY /srv/newrelic.ini

VOLUME ["/srv/filestore", "/srv/backup", "/var/log/ckan"]

EXPOSE 5000

CMD ["/sbin/my_init"]
