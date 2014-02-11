from zope.interface import Interface

class IPlugin(Interface):
    pass

class IRequestClassifier(IPlugin):
    """ On ingress: classify a request.
    """
    def __call__(environ):
        """ environ -> request classifier string

        This interface is responsible for returning a string
        value representing a request classification.

        o 'environ' is the WSGI environment.
        """

class IChallengeDecider(IPlugin):
    """ On egress: decide whether a challenge needs to be presented
    to the user.
    """
    def __call__(environ, status, headers):
        """ args -> True | False

        o 'environ' is the WSGI environment.

        o 'status' is the HTTP status as returned by the downstream
          WSGI application.

        o 'headers' are the headers returned by the downstream WSGI
          application.

        This interface is responsible for returning True if
        a challenge needs to be presented to the user, False otherwise.
        """

class IIdentifier(IPlugin):

    """
    On ingress: Extract credentials from the WSGI environment and
    turn them into an identity.

    On egress (remember): Conditionally set information in the response headers
    allowing the remote system to remember this identity.

    On egress (forget): Conditionally set information in the response
    headers allowing the remote system to forget this identity (during
    a challenge).
    """

    def identify(environ):
        """ On ingress:

        environ -> {   k1 : v1
                       ,   ...
                       , kN : vN
                       } | None

        o 'environ' is the WSGI environment.

        o If credentials are found, the returned identity mapping will
          contain an arbitrary set of key/value pairs.  If the
          identity is based on a login and password, the environment
          is recommended to contain at least 'login' and 'password'
          keys as this provides compatibility between the plugin and
          existing authenticator plugins.  If the identity can be
          'preauthenticated' (e.g. if the userid is embedded in the
          identity, such as when we're using ticket-based
          authentication), the plugin should set the userid in the
          special 'repoze.who.userid' key; no authenticators will be
          asked to authenticate the identity thereafer.

        o Return None to indicate that the plugin found no appropriate
          credentials.

        o Only IIdentifier plugins which match one of the the current
          request's classifications will be asked to perform
          identification.

        o An identifier plugin is permitted to add a key to the
          environment named 'repoze.who.application', which should be
          an arbitrary WSGI application.  If an identifier plugin does
          so, this application is used instead of the downstream
          application set up within the middleware.  This feature is
          useful for identifier plugins which need to perform
          redirection to obtain credentials.  If two identifier
          plugins add a 'repoze.who.application' WSGI application to
          the environment, the last one consulted will"win".
        """

    def remember(environ, identity):
        """ On egress (no challenge required):

        args -> [ (header-name, header-value), ...] | None

        Return a list of headers suitable for allowing the requesting
        system to remember the identification information (e.g. a
        Set-Cookie header).  Return None if no headers need to be set.
        These headers will be appended to any headers returned by the
        downstream application.
        """

    def forget(environ, identity):
        """ On egress (challenge required):

        args -> [ (header-name, header-value), ...] | None

        Return a list of headers suitable for allowing the requesting
        system to forget the identification information (e.g. a
        Set-Cookie header with an expires date in the past).  Return
        None if no headers need to be set.  These headers will be
        included in the response provided by the challenge app.
        """

class IAuthenticator(IPlugin):

    """ On ingress: validate the identity and return a user id or None.
    """

    def authenticate(environ, identity):
        """ identity -> 'userid' | None

        o 'environ' is the WSGI environment.

        o 'identity' will be a dictionary (with arbitrary keys and
          values).
 
        o The IAuthenticator should return a single user id (optimally
          a string) if the identity can be authenticated.  If the
          identify cannot be authenticated, the IAuthenticator should
          return None.

        Each instance of a registered IAuthenticator plugin that
        matches the request classifier will be called N times during a
        single request, where N is the number of identities found by
        any IIdentifierPlugin instances.

        An authenticator must not raise an exception if it is provided
        an identity dictionary that it does not understand (e.g. if it
        presumes that 'login' and 'password' are keys in the
        dictionary, it should check for the existence of these keys
        before attempting to do anything; if they don't exist, it
        should return None).

        An authenticator is permitted to add extra keys to the 'identity'
        dictionary (e.g., to save metadata from a database query, rather
        than requiring a separate query from an IMetadataProvider plugin).
        """

class IChallenger(IPlugin):

    """ On egress: Conditionally initiate a challenge to the user to
        provide credentials.

        Only challenge plugins which match one of the the current
        response's classifications will be asked to perform a
        challenge.
    """

    def challenge(environ, status, app_headers, forget_headers):
        """ args -> WSGI application or None

        o 'environ' is the WSGI environment.

        o 'status' is the status written into start_response by the
          downstream application.

        o 'app_headers' is the headers list written into start_response by the
          downstream application.

        o 'forget_headers' is a list of headers which must be passed
          back in the response in order to perform credentials reset
          (logout).  These come from the 'forget' method of
          IIdentifier plugin used to do the request's identification.

        Examine the values passed in and return a WSGI application
        (a callable which accepts environ and start_response as its
        two positional arguments, ala PEP 333) which causes a
        challenge to be performed.  Return None to forego performing a
        challenge.
        """


class IMetadataProvider(IPlugin):
    """On ingress: When an identity is authenticated, metadata
       providers may scribble on the identity dictionary arbitrarily.
       Return values from metadata providers are ignored.
    """
    
    def add_metadata(environ, identity):
        """
        Add metadata to the identity (which is a dictionary).  One
        value is always guaranteed to be in the dictionary when
        add_metadata is called: 'repoze.who.userid', representing the
        user id of the identity.  Availability and composition of
        other keys will depend on the identifier plugin which created
        the identity.
        """
