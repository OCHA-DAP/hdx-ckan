import ckan.logic as logic
import ckan.model as model
from ckan.common import c

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

    return {"archived": sorted(archived, key=lambda x: x['title']), "ongoing": sorted(ongoing, key=lambda x: x['title'])}

