'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''


def test_strings_in_text(text, search_strings,
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

    for item in search_strings:
        assert item in section, item + ' not in text section'
