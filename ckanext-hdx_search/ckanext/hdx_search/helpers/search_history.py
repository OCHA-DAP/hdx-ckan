import ckan.model as model
import ckan.lib.helpers as h
from ckanext.hdx_search.model import SearchedString
from ckan.plugins import toolkit as tk


_get_action = tk.get_action


def store_search(search_string, user_id):
    if search_string and user_id:
        clean_string = u' '.join([term for term in search_string.split(' ') if term])
        searched_string = SearchedString.by_search_string_and_user(clean_string, user_id)
        if searched_string:
            searched_string.update_last_modified()
        else:
            searched_string = SearchedString(clean_string, user_id)
        searched_string.save()


def num_of_results_for_prev_searches(userobj):
    num_of_results_per_search = []
    if userobj and userobj.id:
        context = {'model': model, 'session': model.Session,
                   'user': userobj.name, 'for_view': True,
                   'auth_user_obj':userobj}

        latest_searched_strings = SearchedString.latest_queries_for_user(userobj.id)
        for s in latest_searched_strings:
            last_search_time = s.last_modified.isoformat() + "Z" # it's in UTC
            data_dict = {
                'q': s.search_string,
                'fq': 'metadata_modified:[{} TO NOW]'.format(last_search_time),
                'rows': 1,
                'start': 0,
            }
            query = _get_action('package_search')(context, data_dict)
            count = query.get('count', 0)
            if count > 0:
                num_of_results_per_search.append({
                    'text': s.search_string,
                    'count': count,
                    'url': h.url_for('search', ext_after_metadata_modified=last_search_time,
                                     ext_search_source='main-nav', q=s.search_string)
                })
            if len(num_of_results_per_search) >= 3:
                break

    return num_of_results_per_search
