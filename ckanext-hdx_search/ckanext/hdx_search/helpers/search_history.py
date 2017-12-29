from ckanext.hdx_search.model import SearchedString


def store_search(search_string, user_id):
    if search_string and user_id:
        clean_string = u' '.join([term for term in search_string.split(' ') if term])
        searched_string = SearchedString.by_search_string_and_user(clean_string, user_id)
        if searched_string:
            searched_string.update_last_modified()
        else:
            searched_string = SearchedString(clean_string, user_id)
        searched_string.save()
