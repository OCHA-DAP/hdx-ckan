""" Configuration parser
"""
from ConfigParser import ConfigParser
from StringIO import StringIO
import logging
from pkg_resources import EntryPoint
import sys

from repoze.who.interfaces import IAuthenticator
from repoze.who.interfaces import IChallengeDecider
from repoze.who.interfaces import IChallenger
from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IMetadataProvider
from repoze.who.interfaces import IPlugin
from repoze.who.interfaces import IRequestClassifier
from repoze.who.middleware import PluggableAuthenticationMiddleware

def _resolve(name):
    if name:
        return EntryPoint.parse('x=%s' % name).load(False)

class WhoConfig:
    def __init__(self, here):
        self.here = here
        self.request_classifier = None
        self.challenge_decider = None
        self.plugins = {}
        self.identifiers = []
        self.authenticators = []
        self.challengers = []
        self.mdproviders = []
        self.remote_user_key = 'REMOTE_USER'

    def _makePlugin(self, name, iface, options=None):
        if options is None:
            options = {}
        obj = _resolve(name)
        if not iface.providedBy(obj):
            obj = obj(**options)
        return obj

    def _getPlugin(self, name, iface):
        obj = self.plugins.get(name)
        if obj is None:
            obj = self._makePlugin(name, iface)
        return obj

    def _parsePluginSequence(self, attr, proptext, iface):
        lines = proptext.split()
        for line in lines:

            if ';' in line:
                plugin_name, classifier = line.split(';')
            else:
                plugin_name = line
                classifier = None

            plugin = self._getPlugin(plugin_name, iface)

            if classifier is not None:
                classifications = getattr(plugin, 'classifications', None)
                if classifications is None:
                    classifications = plugin.classifications = {}
                classifications[iface] = classifier

            attr.append((plugin_name, plugin))

    def parse(self, text):
        if getattr(text, 'readline', None) is None:
            text = StringIO(text)
        cp = ConfigParser(defaults={'here': self.here})
        cp.readfp(text)

        for s_id in [x for x in cp.sections() if x.startswith('plugin:')]:
            plugin_id = s_id[len('plugin:'):]
            options = dict(cp.items(s_id))
            if 'use' in options:
                name = options.pop('use')
                del options['here']
                obj = self._makePlugin(name, IPlugin, options)
                self.plugins[plugin_id] = obj

        if 'general' in cp.sections():
            general = dict(cp.items('general'))

            rc = general.get('request_classifier')
            if rc is not None:
                rc = self._getPlugin(rc, IRequestClassifier)
            self.request_classifier = rc

            cd = general.get('challenge_decider')
            if cd is not None:
                cd = self._getPlugin(cd, IChallengeDecider)
            self.challenge_decider = cd

            ru = general.get('remote_user_key')
            if ru is not None:
                self.remote_user_key = ru

        if 'identifiers' in cp.sections():
            identifiers = dict(cp.items('identifiers'))
            self._parsePluginSequence(self.identifiers,
                                      identifiers['plugins'],
                                      IIdentifier,
                                     )

        if 'authenticators' in cp.sections():
            authenticators = dict(cp.items('authenticators'))
            self._parsePluginSequence(self.authenticators,
                                      authenticators['plugins'],
                                      IAuthenticator,
                                     )

        if 'challengers' in cp.sections():
            challengers = dict(cp.items('challengers'))
            self._parsePluginSequence(self.challengers,
                                      challengers['plugins'],
                                      IChallenger,
                                     )

        if 'mdproviders' in cp.sections():
            mdproviders = dict(cp.items('mdproviders'))
            self._parsePluginSequence(self.mdproviders,
                                      mdproviders['plugins'],
                                      IMetadataProvider,
                                     )


_LEVELS = {'debug': logging.DEBUG,
           'info': logging.INFO,
           'warning': logging.WARNING,
           'error': logging.ERROR,
          }

def make_middleware_with_config(app, global_conf, config_file,
                                log_file=None, log_level=None):
    parser = WhoConfig(global_conf['here'])
    parser.parse(open(config_file))
    log_stream = None

    if log_file is not None:
        if log_file.lower() == 'stdout':
            log_stream = sys.stdout
        else:
            log_stream = open(log_file, 'wb')

    if log_level is None:
        log_level = logging.INFO
    else:
        log_level = _LEVELS[log_level.lower()]

    return PluggableAuthenticationMiddleware(
                app,
                parser.identifiers,
                parser.authenticators,
                parser.challengers,
                parser.mdproviders,
                parser.request_classifier,
                parser.challenge_decider,
                log_stream,
                log_level,
                parser.remote_user_key,
           )
