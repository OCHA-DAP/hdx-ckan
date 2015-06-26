'''
Tests for sitemap.
'''

import logging
import unittest
from StringIO import StringIO
import json
from lxml import etree
import datetime

from pylons import config
import ckan.config as ckanconfig
import webtest

from ckan.model import Session, Package, Resource
import ckan.model as model
from ckan.tests import CreateTestData
import ckan.lib.create_test_data as ctd
from ckan.lib.helpers import url_for
from ckan.logic.auth.get import package_show
from ckan.tests.functional.base import FunctionalTestCase


import testdata

log = logging.getLogger(__file__)

siteschema = etree.XMLSchema(etree.parse(StringIO(testdata.sitemap)))
indexschema = etree.XMLSchema(etree.parse(StringIO(testdata.sitemapindex)))

def _get_test_app():
    config['ckan.legacy_templates'] = False
    app = ckanconfig.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app

class TestSitemap(FunctionalTestCase, unittest.TestCase):
    
    @classmethod
    def setup_class(cls):
        """
        Remove any initial sessions.
        """
        Session.remove()
        cls.original_config = config.copy()
        plugins = set(config['ckan.plugins'].strip().split())
        plugins.add('sitemap')
        config['ckan.plugins'] = ' '.join(plugins)
        cls.app = _get_test_app()
        CreateTestData.create()
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='view')
        cls.cont = cls.app.get(url)
        cls.content_file = StringIO(cls.cont.body)

    @classmethod
    def teardown_class(cls):
        """
        Tear down, remove the session.
        """
        CreateTestData.delete()
        Session.remove()

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)
    
    def test_controller(self):
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='view')
        self.cont = self.app.get(url)
        self.content_file = StringIO(self.cont.body)
        assert self.cont.response.status == "200 OK"

    def test_validity_index(self):
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='view')
        self.cont = self.app.get(url)
        print self.cont.body
        self.content_file = StringIO(self.cont.body)
        indexschema.assertValid(etree.parse(self.content_file))
        assert indexschema.validate(etree.parse(self.content_file))

    def test_validity_map(self):
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='index', page=1)
        self.cont = self.app.get(url)
        print self.cont.body
        self.content_file = StringIO(self.cont.body)
        siteschema.assertValid(etree.parse(self.content_file))
        assert siteschema.validate(etree.parse(self.content_file))

    def test_packages(self):
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='index', page=1)
        self.cont = self.app.get(url)
        self.content_file = StringIO(self.cont.body)
        tree = etree.parse(self.content_file)
        self.assert_("annakarenina" in self.cont.body)
        log.debug(self.cont.body)
        pkg = Session.query(Package).all()[0]
        urli = config.get('ckan.site_url') + url_for(controller='package',
                                                     action='read',
                                                     id = pkg.name)
        self.assert_(tree.getroot()[0][0].text == urli)
        # Needs to be created today as test data is too
        pkgdate = pkg.latest_related_revision.timestamp.strftime('%Y-%m-%d')
        self.assert_(tree.getroot()[0][1].text == pkgdate)
        resurl = config.get('ckan.site_url') + url_for(controller='package',
                                                       action='resource_read',
                                                       id = pkg.name,
                                                       resource_id = pkg.resources[0].id)
        self.assert_(tree.getroot()[1][0].text == resurl)

    def _create_pkg(self):
        model.repo.new_revision()
        pkg = Package.get('annakarenina')
        pkg.name = "fookarenina"
        pkg.add_resource('www.google.com',description='foo', name="foo")
        Session.add(pkg)
        Session.commit()
        return pkg


    def test_zcache(self):
        url = url_for(controller="ckanext.sitemap.controller:SitemapController",
                      action='view')
        cont1 = self.app.get(url)
        cont2 = self.app.get(url)
        self.assert_(cont1.body == cont2.body)
        log.debug(cont1.body)
        pkg = self._create_pkg()
        log.debug(len(pkg.resources))
        cont2 = self.app.get(url)
        log.debug(cont2.body)
        self.assert_(cont1.body == cont2.body)