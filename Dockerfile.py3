FROM python:3.8-slim

COPY . /srv/ckan/
WORKDIR /srv/ckan

# Install required system packages
RUN apt-get -q -y update \
    && DEBIAN_FRONTEND=noninteractive apt-get -q -y upgrade \
    && apt-get -q -y install \
        libmagic1 \
        libpq-dev \
        libxml2-dev \
        libxslt-dev \
        libgeos-dev \
        libssl-dev \
        libffi-dev \
        postgresql-client \
        build-essential \
        gettext-base \
        git-core \
        vim \
        wget

RUN mkdir -p /var/log/ckan /srv/filestore && \
    cd /srv/ckan && \
    python -m pip install --upgrade pip && \
    pip install -r requirement-setuptools.txt && \
    pip install --upgrade -r requirements.txt && \
    pip install --upgrade gunicorn && \
    chmod +x setup_py3_helper.sh && \
    ./setup_py3_helper.sh

RUN DEBIAN_FRONTEND=noninteractive apt-get -qq -y remove \
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
    apt-get clean
