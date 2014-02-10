import cgi
import urlparse
import cgitb
import sys
from itertools import chain
from zope.interface import implements

from repoze.who.interfaces import IChallenger
from repoze.who.interfaces import IIdentifier
from repoze.who.interfaces import IAuthenticator

from webob import Request, Response

import openid
from openid.store import memstore, filestore, sqlstore
from openid.consumer import consumer
from openid.oidutil import appendArgs
from openid.cryptutil import randomString
from openid.fetchers import setDefaultFetcher, Urllib2Fetcher
from openid.extensions import pape, sreg, ax



class OpenIdIdentificationPlugin(object):
    """The repoze.who OpenID plugin
    
    This class contains 3 plugin types and is thus implementing
    IIdentifier, IChallenger and IAuthenticator.
    (check the `repoze.who documentation <http://static.repoze.org/bfgdocs/>`_
    for what all these plugin types do.)
    
    """


    implements(IChallenger, IIdentifier, IAuthenticator)

    def __init__(self, store, 
                    openid_field, 
                    error_field = '',
                    store_file_path='',
                    session_name = '',
                    login_handler_path = '',
                    logout_handler_path = '',
                    login_form_url = '',
                    logged_in_url = '',
                    logged_out_url = '',
                    came_from_field = '',
                    rememberer_name = '',
                    sql_associations_table = '',
                    sql_nonces_table = '',
                    sql_connstring = '',
                    ax_require = '',
                    ax_optional = '',
                    sreg_require = '',
                    sreg_optional = ''):

        self.rememberer_name = rememberer_name
        self.login_handler_path = login_handler_path
        self.logout_handler_path = logout_handler_path
        self.login_form_url = login_form_url
        self.session_name = session_name
        self.error_field = error_field
        self.came_from_field = came_from_field
        self.logged_out_url = logged_out_url
        self.logged_in_url = logged_in_url
        self.ax_require = {}
        
        for item in ax_require.split():
            key, value = item.split("=")
            self.ax_require[key] = value
            
        self.ax_optional = {}
        for item in ax_optional.split():
            key, value = item.split("=")
            self.ax_optional[key] = value
            
        self.sreg_require = [a.strip() for a in sreg_require.split()]
        self.sreg_optional = [a.strip() for a in sreg_optional.split()]
        
        # for the SQL store
        self.sql_associations_table = sql_associations_table
        self.sql_nonces_table = sql_nonces_table
        self.sql_connstring = sql_connstring
        
        # set up the store
        if store==u"file":
            self.store = filestore.FileOpenIDStore(store_file_path)
        elif store==u"mem":
            self.store = memstore.MemoryStore()
        elif store==u"sql":
            # TODO: This does not work as we need a connection, not a string
            self.store = sqlstore.SQLStore(sql_connstring, sql_associations_table, sql_connstring)
        self.openid_field = openid_field
            
    def _get_rememberer(self, environ):
        rememberer = environ['repoze.who.plugins'][self.rememberer_name]
        return rememberer

    def get_consumer(self,environ):
        session = environ.get(self.session_name,{})
        return consumer.Consumer(session,self.store)
        
    def redirect_to_logged_in(self, environ):
        """redirect to came_from or standard page if login was successful"""
        request = Request(environ)
        came_from = request.params.get(self.came_from_field,'')
        if came_from!='':
            url = came_from
        else:
            url = self.logged_in_url
        res = Response()
        res.status = 302
        res.location = url
        environ['repoze.who.application'] = res    

    # IIdentifier
    def identify(self, environ):
        """this method is called when a request is incoming.

        After the challenge has been called we might get here a response
        from an openid provider.

        """

        request = Request(environ)
        
        # first test for logout as we then don't need the rest
        if request.path == self.logout_handler_path:
            res = Response()
            # set forget headers
            for a,v in self.forget(environ,{}):
                res.headers.add(a,v)
            res.status = 302
            res.location = self.logged_out_url
            environ['repoze.who.application'] = res
            return {}

        identity = {}

        # first we check we are actually on the URL which is supposed to be the
        # url to return to (login_handler_path in configuration)
        # this URL is used for both: the answer for the login form and
        # when the openid provider redirects the user back.
        if request.path == self.login_handler_path:

        # in the case we are coming from the login form we should have 
        # an openid in here the user entered
            open_id = request.params.get(self.openid_field, None)
            if environ['repoze.who.logger'] is not None:
                environ['repoze.who.logger'].debug('checking openid results for : %s ' %open_id)
            
            if open_id is not None:
                open_id = open_id.strip()
            
            # we don't do anything with the openid we found ourselves but we put it in here
            # to tell the challenge plugin to initiate the challenge
            identity['repoze.whoplugins.openid.openid'] = environ['repoze.whoplugins.openid.openid'] = open_id
        
            # this part now is for the case when the openid provider redirects
            # the user back. We should find some openid specific fields in the request.
            mode=request.params.get("openid.mode", None)
            if mode=="id_res":
                oidconsumer = self.get_consumer(environ)
                info = oidconsumer.complete(request.params, request.url)
                if info.status == consumer.SUCCESS:

                    fr = ax.FetchResponse.fromSuccessResponse(info)
                    if fr is not None:
                        items = chain(self.ax_require.items(), self.ax_optional.items())
                        for key, value in items:
                            try:
                                identity['repoze.who.plugins.openid.' + key] = fr.get(value)
                            except KeyError:
                                pass
                    
                    fr = sreg.SRegResponse.fromSuccessResponse(info)
                    if fr is not None:
                        items = chain(self.sreg_require, self.sreg_optional)
                        for key in items:
                            try:
                                identity['repoze.who.plugins.openid.' + key] = fr.get(key)
                            except KeyError:
                                pass

                    environ['repoze.who.logger'].info('openid request successful for : %s ' %open_id)
                    
                    display_identifier = info.identity_url
                    
                    # remove this so that the challenger is not triggered again
                    del environ['repoze.whoplugins.openid.openid']
                    
                    # store the id for the authenticator
                    identity['repoze.who.plugins.openid.userid'] = display_identifier
                    
                    # now redirect to came_from or the success page
                    self.redirect_to_logged_in(environ)
                    return identity
                    
                # TODO: Do we have to check for more failures and such?
                # 
            elif mode=="cancel":
                # cancel is a negative assertion in the OpenID protocol,
                # which means the user did not authorize correctly.
                environ['repoze.whoplugins.openid.error'] = 'OpenID authentication failed.'
                pass
        return identity

    # IIdentifier
    def remember(self, environ, identity):
        """remember the openid in the session we have anyway"""
        rememberer = self._get_rememberer(environ)
        r = rememberer.remember(environ, identity)
        return r

    # IIdentifier
    def forget(self, environ, identity):
        """forget about the authentication again"""
        rememberer = self._get_rememberer(environ)
        return rememberer.forget(environ, identity)

    # IChallenge
    def challenge(self, environ, status, app_headers, forget_headers):
        """the challenge method is called when the ``IChallengeDecider``
        in ``classifiers.py`` returns ``True``. This is the case for either a 
        ``401`` response from the client or if the key 
        ``repoze.whoplugins.openid.openidrepoze.whoplugins.openid.openid``
        is present in the WSGI environment.
        The name of this key can be adjusted via the ``openid_field`` configuration
        directive.

        The latter is the case when we are coming from the login page where the
        user entered the openid to use.

        ``401`` can come back in any case and then we simply redirect to the login
        form which is configured in the who configuration as ``login_form_url``.

        TODO: make the environment key to check also configurable in the challenge_decider.

        For the OpenID flow check `the OpenID library documentation 
        <http://openidenabled.com/files/python-openid/docs/2.2.1/openid.consumer.consumer-module.html>`_

        """

        request = Request(environ)
        
        # check for the field present, if not redirect to login_form
        if not request.params.has_key(self.openid_field):
            # redirect to login_form
            res = Response()
            res.status = 302
            res.location = self.login_form_url+"?%s=%s" %(self.came_from_field, request.url)
            return res

        # now we have an openid from the user in the request 
        openid_url = request.params[self.openid_field]
        if environ['repoze.who.logger'] is not None:
            environ['repoze.who.logger'].debug('starting openid request for : %s ' %openid_url)
        
        try:
        # we create a new Consumer and start the discovery process for the URL given
        # in the library openid_request is called auth_req btw.
            openid_request = self.get_consumer(environ).begin(openid_url)
            
            if len(self.ax_require.values()) or len(self.ax_optional.values()):
                fetch_request = ax.FetchRequest()
                for value in self.ax_require.values():
                    fetch_request.add(ax.AttrInfo(value, required=True))
                for value in self.ax_optional.values():
                    fetch_request.add(ax.AttrInfo(value, required=False))
                openid_request.addExtension(fetch_request)
            
            if len(self.sreg_require) or len(self.sreg_optional):
                sreq = sreg.SRegRequest(required=self.sreg_require, optional=self.sreg_optional)
                openid_request.addExtension(sreq)
            

        except consumer.DiscoveryFailure, exc:
            # eventually no openid server could be found
            environ[self.error_field] = 'Error in discovery: %s' %exc[0]
            environ['repoze.who.logger'].info('Error in discovery: %s ' %exc[0])     
            return self._redirect_to_loginform(environ)
        except KeyError, exc:
            # TODO: when does that happen, why does plone.openid use "pass" here?
            environ[self.error_field] = 'Error in discovery: %s' %exc[0]
            environ['repoze.who.logger'].info('Error in discovery: %s ' %exc[0])
            return self._redirect_to_loginform(environ)
            return None
           
        # not sure this can still happen but we are making sure.
        # should actually been handled by the DiscoveryFailure exception above
        if openid_request is None:
            environ[self.error_field] = 'No OpenID services found for %s' %openid_url
            environ['repoze.who.logger'].info('No OpenID services found for: %s ' %openid_url)
            return self._redirect_to_loginform(environ)
       
        # we have to tell the openid provider where to send the user after login
        # so we need to compute this from our path and application URL
        # we simply use the URL we are at right now (which is the form)
        # this will be captured by the repoze.who identification plugin later on
        # it will check if some valid openid response is coming back
        # trust_root is the URL (realm) which will be presented to the user
        # in the login process and should be your applications url
        # TODO: make this configurable?
        # return_to is the actual URL to be used for returning to this app
        return_to = request.path_url # we return to this URL here
        trust_root = request.application_url
        if environ['repoze.who.logger'] is not None:
            environ['repoze.who.logger'].debug('setting return_to URL to : %s ' %return_to)
        
        # TODO: usually you should check openid_request.shouldSendRedirect()
        # but this might say you have to use a form redirect and I don't get why
        # so we do the same as plone.openid and ignore it.

        # TODO: we might also want to give the application some way of adding
        # extensions to this message.
        redirect_url = openid_request.redirectURL(trust_root, return_to) 
        # # , immediate=False)
        res = Response()
        res.status = 302
        res.location = redirect_url
        if environ['repoze.who.logger'] is not None:
            environ['repoze.who.logger'].debug('redirecting to : %s ' %redirect_url)

        # now it's redirecting and might come back via the identify() method
        # from the openid provider once the user logged in there.
        return res
        
    def _redirect_to_loginform(self, environ={}):
        """redirect the user to the login form"""
        res = Response()
        res.status = 302
        q=''
        ef = environ.get(self.error_field, None)
        if ef is not None:
                q='?%s=%s' %(self.error_field, ef)
        res.location = self.login_form_url+q
        return res
        
                
    # IAuthenticator
    def authenticate(self, environ, identity):
        """dummy authenticator
        
        This takes the openid found and uses it as the userid. Normally you would want
        to take the openid and search a user for it to map maybe multiple openids to a user.
        This means for you to simply implement something similar to this. 
        
        """
        if identity.has_key("repoze.who.plugins.openid.userid"):
                environ['repoze.who.logger'].info('authenticated : %s ' %identity['repoze.who.plugins.openid.userid'])
                return identity.get('repoze.who.plugins.openid.userid')


    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, id(self))

