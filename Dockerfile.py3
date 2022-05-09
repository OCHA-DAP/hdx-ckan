FROM ubuntu:focal
# FROM public.ecr.aws/unocha/debian-base-s6:11-slim

ARG S6_VERSION=v2.2.0.3

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en_US \
    LC_ALL=en_US.UTF-8 \
    HDX_CKAN_WORKERS=4 \
    INI_FILE=/etc/ckan/prod.ini \
    HDX_CACHE_DIR=/srv/cache \
    HDX_LOG_LEVEL=INFO

WORKDIR /srv/ckan

COPY . .

# Install required system packages
RUN apt-get -qq -y update && \
    # locales
    apt-get -qq -y install locales && \
    echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen && \
    cp docker/locale /etc/default/locale && \
    locale-gen en_US.UTF-8 && \
    dpkg-reconfigure locales && \
    update-locale LANGUAGE=en_US.UTF-8 LC_ALL=en_US.UTF-8 && \
    apt-get -q -y update && \
    apt-get -q -y install \
        build-essential \
        curl \
        gettext-base \
        git-core \
        gpg \
        iputils-ping \
        libmagic1 \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libssl-dev \
        libffi-dev \
        nano \
        net-tools \
        postgresql-client \
        procps \
        psmisc \
        python3 \
        python3-pip \
        vim \
        wget && \
    # make python3 and pip3 available as python and pip
    ln -sf /usr/bin/python3 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    # perpare nginx unit installation
    curl --output /usr/share/keyrings/nginx-keyring.gpg https://unit.nginx.org/keys/nginx-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/nginx-keyring.gpg] https://packages.nginx.org/unit/ubuntu/ focal unit" > /etc/apt/sources.list.d/unit.list && \
    echo "deb-src [signed-by=/usr/share/keyrings/nginx-keyring.gpg] https://packages.nginx.org/unit/ubuntu/ focal unit" >> /etc/apt/sources.list.d/unit.list && \
    # perpare Node 16 installation
    curl -sL https://deb.nodesource.com/setup_16.x | bash - && \
    # install Node and nginx unit
    apt-get -qq -y install \
      nodejs \
      unit unit-python3.8 && \
    ln -sf /usr/lib/unit/modules/python3.8.unit.so /usr/lib/unit/modules/python.unit.so && \
    # install lessc
    npm install -g less@3.13.1 && \
    # prepare files and folders
    mkdir -p /var/log/ckan /srv/filestore /etc/services.d/unit /etc/ckan && \
    cd /srv/ckan && \
    python -m pip install --upgrade pip && \
    pip install -r requirement-setuptools.txt && \
    pip install --upgrade -r requirements.txt && \
    pip install newrelic && \
    chmod +x run_pytest_with_coverage.sh && \
    chmod +x setup_py3_helper.sh && \
    ./setup_py3_helper.sh && \
    newrelic-admin generate-config LICENSE_KEY /srv/newrelic.ini && \
    chown -R www-data ckan/public/base/i18n && \
    cp -a docker/run_unit /etc/services.d/unit/run && \
    chown www-data:www-data -R /var/log/ckan /srv/filestore && \
    cp -a docker/hdxckantool-ng.py /srv/hdxckantool-ng.py && \
    chmod +x /srv/hdxckantool-ng.py && \
    ln -s /srv/hdxckantool-ng.py /usr/sbin/hdxckantool && \
    echo "application/vnd.geo+json       geojson" >> /etc/mime.types && \
    apt-get -qq -y remove \
        build-essential \
        gpg \
        libffi-dev \
        libpq-dev \
        libssl-dev \
        libxml2-dev \
        libxslt1-dev \
        libyaml-dev \
        zlib1g-dev \
        python-dev && \
    apt-get -y autoremove && \
    apt-get clean && \
    rm -rf \
        /root/.cache \
        /root/.npm \
        /usr/local/man \
        /usr/share/doc \
        /usr/share/man \
        /var/lib/apt/lists/* \
        /var/tmp/* \
        /tmp/* && \
    S6_ARCH=$(uname -m | sed 's/x86_64/amd64/') && \
    echo "Installing s6 version: $S6_VERSION for $S6_ARCH" && \
    curl -o /tmp/s6-overlay.tar.gz -jkSL https://github.com/just-containers/s6-overlay/releases/download/${S6_VERSION}/s6-overlay-${S6_ARCH}.tar.gz && \
    tar xzf /tmp/s6-overlay.tar.gz -C / && \
    rm -f /tmp/s6-overlay.tar.gz && \
    ln -sf /usr/bin/sh /bin/sh


VOLUME ["/srv/filestore", "/srv/backup", "/var/log/ckan"]

EXPOSE 5000

ENTRYPOINT ["/init"]

CMD []
