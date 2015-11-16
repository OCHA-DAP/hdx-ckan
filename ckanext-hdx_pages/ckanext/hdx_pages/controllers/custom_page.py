import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model

from ckan.common import _, c, g, request, response


class PagesController(base.BaseController):
    def new(self, data=None, errors=None, error_summary=None):
        errors = errors or {}
        data_dict = {}
        data_dict['content_type'] = [{'value': 'empty', 'text': _('Select content type')},
                                     {'value': 'map', 'text': _('Map')},
                                     {'value': 'key-figures', 'text': _('Key Figures')},
                                     {'value': 'interactive-data', 'text': _('Interactive Data')},
                                     {'value': 'data-list', 'text': _('Data List')}]
        vars = {'data': data, 'data_dict': data_dict, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}
        params = request.params
        return base.render('pages/edit_page.html', extra_vars=vars)

    def edit(self, id):
        return None

    def read(self, id, type):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }
        page_dict = logic.get_action('page_show')(context, {'id': id})

        if not type or type != page_dict.get('type'):
            base.abort(404, _('Wrong page type'))
        else:
            return base.render('pages/read_page.html')
