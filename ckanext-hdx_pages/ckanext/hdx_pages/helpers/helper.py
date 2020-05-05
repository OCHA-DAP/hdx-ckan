import ckan.logic as logic
import ckan.model as model
from ckan.common import c
from urlparse import parse_qs, urlparse


def hdx_events_list():
    context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}

    events = logic.get_action('page_list')(context, {})
    archived = []
    ongoing = []
    for e in events:
        if e.get("type") == 'event':
            if e.get("status") == 'ongoing':
                ongoing.append(e)
            if e.get("status") == 'archived':
                archived.append(e)

    return {"archived": sorted(archived, key=lambda x: x['title']),
            "ongoing": sorted(ongoing, key=lambda x: x['title'])}


def _compute_iframe_style(section):
    style = 'width: 100%; '
    max_height = section.get('max_height')
    height = max_height if max_height else '400px'
    style += 'max-height: {}; '.format(max_height) if max_height else ''
    style += 'height: {}; '.format(height)
    section['style'] = style
    return section


def _find_dataset_filters(url):
    filters = parse_qs(urlparse(url).query)
    return filters
