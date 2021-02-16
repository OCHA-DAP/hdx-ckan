#!/bin/bash

mv -f requirements-py2.txt requirements-py2-tmp.txt
grep -v "github" requirements-py2-tmp.txt >> requirements-py2.txt
python setup.py develop
mv -f requirements-py2-tmp.txt requirements-py2.txt

for p in $(ls -d ckanext-*); do cd /srv/ckan/$p; python setup.py develop; done
cd /srv/ckan

