'''
Created on Nov 12, 2014

@author: alexandru-m-g
'''


def are_strings_in_text(text, search_strings,
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


def count_string_occurences(text, search_item,
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
