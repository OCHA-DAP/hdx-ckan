class MaintenanceResponse(object):
    """
    Imagine an apache config like this:

    ::

        RewriteLog "/var/log/apache2/rewrite.log" 
        RewriteLogLevel 3
        RewriteEngine On
        RewriteRule ^(.*)/new /return_503 [PT,L]
        RewriteRule ^(.*)/create /return_503 [PT,L]
        RewriteRule ^(.*)/edit /return_503 [PT,L]
        RewriteCond %{REQUEST_METHOD} !^GET$ [NC]
        RewriteRule (.*) /return_503 [PT,L]

    This middleware component will intercept any calls to ``/return_503`` so that 
    the correct response can be sent directly from a re-write rule in order to
    allow maintenance configuration to be maintained in the Apache config with no
    dependency on your WSGI application.

    This in turn allows you to control which bits of an application are
    restricted during maintenance.

    You can then deploy an instance like this (although this isn't how I like to do it):

    ::

        application = MaintenanceResponse(application)

    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('PATH_INFO', '') == '/return_503':
            return self.send_503(environ, start_response)
        return self.app(environ, start_response)

    def send_503(self, environ, start_response):
        start_response('503 Unavailable due to maintenance', [('Content-type', 'text/html')])
        return ["""
<html>
<head>
    <title>503 Unavailable due to maintenance</title>
</head>
<body>
<h1>503 Unavailable due to maintenance</h1>

<p>The site is currently undergoing maintenance. Please try again later.</p>
</body>
</html>
        """]


class MountWSGIScriptAlias(object):
    """
    If you have a WSGI application and you only want to expose part of it you
    can set up a ``WSGIScriptAlias`` for the part you want to expose. You'll then
    need to alter the ``SCRIPT_NAME`` and ``PATH_INFO`` so that the WSGI
    application serves the part that has been requested, instead of the root URL.

    For example, imagine wanting to serve all URLs under ``/api``. Your Apache 
    config would contain this:

    ::

        WSGIScriptAlias /api /path/to/deploy.py

    Then in ``deploy.py`` you'd wrap your ``application`` object lke this:

    ::

        application = MountWSGIScriptAlias(application, '/api')

    This middleware writes the changes it makes to the ``wsgi.errors`` log.    
    """
    def __init__(self, app, mount_path):
        self.app = app
        self.mount_path = mount_path

    def __call__(self, environ, start_response):
        environ['wsgi.errors'].write('Orig PATH_INFO: %s'%environ.get('PATH_INFO'))
        environ['wsgi.errors'].write('Orig SCRIPT_NAME: %s'%environ.get('SCRIPT_NAME'))
        environ['PATH_INFO'] = '/api'+environ['PATH_INFO']
        environ['SCRIPT_NAME'] = ''
        environ['wsgi.errors'].write('New PATH_INFO: %s'%environ.get('PATH_INFO'))
        environ['wsgi.errors'].write('New SCRIPT_NAME: %s'%environ.get('SCRIPT_NAME'))
        return self.app(environ, start_response)

