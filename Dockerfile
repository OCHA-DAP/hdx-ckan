FROM unocha/hdx-base-ckan:latest

ENV HDX_CKAN_WORKERS=4

COPY . /srv/ckan/

WORKDIR /srv/ckan

RUN rm -rf /usr/local/man && \
    mkdir -p /var/log/ckan /srv/filestore /etc/service/ckan /srv/pgb /etc/service/pgb && \
    cp -a docker/helper_ckan.py /srv/helper.py && \
    cp -a docker/run_ckan /etc/service/ckan/run && \
    cp -a docker/gunicorn_conf.py /srv/ && \
    chmod +x /etc/service/ckan/run && \
    chown www-data:www-data -R /var/log/ckan /srv/filestore && \
    curl -s -o /srv/hdxckantool.py https://raw.githubusercontent.com/OCHA-DAP/hdx-tools/master/hdxckantool.py && \
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
