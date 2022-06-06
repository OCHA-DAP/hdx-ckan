import ckan.plugins.toolkit as tk

config = tk.config
request = tk.request

MIMETYPE_LIST = config.get('hdx.http_headers.mimetypes').split(',')

ROUTES_LIST = config.get('hdx.http_headers.routes').split(',')


# use app.after_request(set_http_headers)
def set_http_headers(response):
    if response.mimetype and response.mimetype in MIMETYPE_LIST:
        url_contains_route = False
        if request and request.url:
            url_contains_route = any(route in request.url for route in ROUTES_LIST)
        if not url_contains_route:
            response.headers[b'X-Frame-Options'] = b'SAMEORIGIN'
    return response
