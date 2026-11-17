'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''
import re

import ckan.plugins.toolkit as tk


def get_csrf_form_field(client, page_url=None):
    '''
    Loads a page that renders ``h.csrf_input()`` (the login page by default) and returns
    ``{field_name: token}``, ready to merge into the POST data.

    The token belongs to the client's session, so POST with the same ``client``.
    ``CKANTestApp.post()`` opens a new client, without cookies, on every call.
    '''
    field_name = tk.config.get('WTF_CSRF_FIELD_NAME')
    response = client.get(page_url or tk.h.url_for('hdx_signin.login'))
    match = re.search(rf'name="{re.escape(field_name)}" value="([^"]+)"', response.body)
    assert match, 'CSRF field not found on the page'
    return {field_name: match.group(1)}


def post_with_csrf(app, url, data=None, **kwargs):
    '''
    Like ``CKANTestApp.post()``, but adds a valid CSRF token to ``data``.
    The token is fetched anonymously, so ``kwargs`` (e.g. ``headers``) only apply to the POST.
    '''
    client = app.test_client()
    post_data = dict(data or {})
    post_data.update(get_csrf_form_field(client))
    return client.post(url, data=post_data, **kwargs)


def _normalize_whitespace(text):
    return re.sub(r'\s+', ' ', text).strip()

def are_strings_in_text(text, search_strings,
                        begin_str=None, end_str=None, normalize=False):

    if normalize:
        text = _normalize_whitespace(text)
        if begin_str:
            begin_str = _normalize_whitespace(begin_str)
        if end_str:
            end_str = _normalize_whitespace(end_str)
        search_strings = [_normalize_whitespace(s) for s in search_strings]

    start = 0
    end = len(text)
    if begin_str:
        start = text.find(begin_str)
    if end_str:
        end = text.find(end_str, start)

    assert start >= 0, 'Begin of string not found'
    assert end >= 0, 'End of string not found'

    section = text[start + len(begin_str):end]

    for item in search_strings:
        assert item in section, item + ' not in text section'


# def strings_not_in_text(text, search_strings,
#                         begin_str=None, end_str=None):
#
#     start = 0
#     end = len(text)
#     if begin_str:
#         start = text.find(begin_str)
#     if end_str:
#         end = text.find(end_str, start)
#
#     assert start >= 0
#     assert end >= 0
#
#     section = text[start + len(begin_str):end]
#
#     for item in search_strings:
#         assert item not in section, item + ' exists in text section'


def count_string_occurrences(text, search_item,
                            begin_str=None, end_str=None):
    start = 0
    end = len(text)
    if begin_str:
        start = text.find(begin_str)
    if end_str:
        end = text.find(end_str, start)

    assert start >= 0
    assert end >= 0

    section = text[start + len(begin_str):end]
    count = section.count(search_item)

    return count


def test_string_checks():
    page = 'lorep ipsum <section class="search-list list-items">lorep ipsumlorep name="q" ipsumlorep ipsum</section>'

    begin_str = '<section class="search-list list-items">'
    end_str = '</section>'
    search_item = 'name="q"'

    count = count_string_occurrences(page, search_item, begin_str, end_str)
    assert count == 1, 'There should be exactly one input with name q in the form'

    page = 'lorep ipsum <section class="search-list list-items"> /dataset lorep Test Dataset 1 name="q" ipsumlorep test_dataset_1</section>'
    search_strings = ['/dataset', 'Test Dataset 1', 'test_dataset_1']

    are_strings_in_text(page, search_strings, begin_str, end_str)
