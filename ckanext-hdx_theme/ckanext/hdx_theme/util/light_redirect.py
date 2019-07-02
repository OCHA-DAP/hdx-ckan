import logging

from flask import make_response
from decorator import decorator

import ua_parser.user_agent_parser as useragent

import ckan.plugins.toolkit as tk
from ckan.common import response

redirect = tk.redirect_to
request = tk.request

FORCE_REDIRECT_COOKIE = 'hdx_force_layout'
FORCE_REDIRECT_URL_PARAM = 'force_layout'
DESKTOP_LAYOUT = 'desktop'
LIGHT_LAYOUT = 'light'
LAYOUTS = {DESKTOP_LAYOUT, LIGHT_LAYOUT}

log = logging.getLogger(__name__)

@decorator
def check_redirect_needed(original_action, *args, **kw):
    if hasattr(request, 'blueprint'): # flask controller
        ua_dict = useragent.Parse(request.user_agent.string)
        is_flask = True
    else: # pylons controller
        ua_dict = useragent.Parse( request.user_agent if request.user_agent else '')
        is_flask = False
    os = ua_dict.get('os', {}).get('family') # type: str
    path = request.full_path if is_flask else request.path_qs
    ua_is_mobile = os and os.lower() in {'android', 'ios'}
    should_redirect = __should_redirect(path, ua_is_mobile)
    if should_redirect and not path.startswith('/m'):
        light_url = '/m' + path
        return redirect(light_url)
    elif should_redirect and path.startswith('/m'):
        standard_url = path[2:]
        return redirect(standard_url)
    else:
        result = original_action(*args, **kw)
        new_cookie_value = __cookie_value_to_set()
        if is_flask and new_cookie_value:
            result = make_response(result)
            result.set_cookie(FORCE_REDIRECT_COOKIE, new_cookie_value)
        if not is_flask and new_cookie_value:
            response.set_cookie(FORCE_REDIRECT_COOKIE, new_cookie_value)
        return result


def __should_redirect(path, ua_is_mobile):
    '''
    The order of priorities: 1) URL param 2) Existing cookie 3) User agent
    :param path: URL path including arguments, Ex: /m/datatset/dataset_name?force-layout=light
    :type path: str
    :param ua_is_mobile: whether the user agent seems to suggest a mobile device
    :type ua_is_mobile: bool
    :return:
    :rtype: bool
    '''
    request_is_on = LIGHT_LAYOUT if path.startswith('/m') else DESKTOP_LAYOUT
    request_param = request.params.get(FORCE_REDIRECT_URL_PARAM)
    cookie_layout = request.cookies.get(FORCE_REDIRECT_COOKIE)
    ua_layout = LIGHT_LAYOUT if ua_is_mobile else DESKTOP_LAYOUT
    # checking url params
    if request_param and request_param in LAYOUTS:
        return request_param != request_is_on
    # checking cookies
    elif cookie_layout and cookie_layout in LAYOUTS:
        return cookie_layout != request_is_on
    # checking user agent
    elif ua_layout != request_is_on:
        return True

    return False


def __cookie_value_to_set():
    new_value = request.params.get(FORCE_REDIRECT_URL_PARAM)
    existing_value = request.cookies.get(FORCE_REDIRECT_COOKIE)
    if new_value in LAYOUTS and new_value != existing_value:
        return new_value
    return None
