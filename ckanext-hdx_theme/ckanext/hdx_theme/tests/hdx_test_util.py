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


def test_string_checks():
    page = 'lorep ipsum <section class="search-list list-items">lorep ipsumlorep name="q" ipsumlorep ipsum</section>'

    begin_str = '<section class="search-list list-items">'
    end_str = '</section>'
    search_item = 'name="q"'

    count = count_string_occurences(page, search_item, begin_str, end_str)
    assert count == 1, 'There should be exactly one input with name q in the form'

    page = 'lorep ipsum <section class="search-list list-items"> /dataset lorep Test Dataset 1 name="q" ipsumlorep test_dataset_1</section>'
    search_strings = ['/dataset', 'Test Dataset 1', 'test_dataset_1']

    are_strings_in_text(page, search_strings, begin_str, end_str)
