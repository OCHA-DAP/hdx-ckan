'''
Created on Jan 14, 2015

@author: alexandru-m-g
'''

def sort_results_case_insensitive(results, sort_by):
    if results:
        if sort_by == 'title asc':
            return sorted(results, key=lambda x: x.get('title','').lower())
        elif sort_by == 'title desc':
            return sorted(results, key=lambda x: x.get('title','').lower(), reverse=True)
    return results