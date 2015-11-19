import json
import ckan.lib.base as base
from ckan.common import _, c, g, request, response
import ckan.logic as logic
import ckan.model as model

get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
abort = base.abort

checked = 'checked="checked"'


class PagesController(base.BaseController):
    def new(self, data=None, errors=None, error_summary=None):

        context, extra_vars = self._init_data(data, error_summary, errors)

        try:
            check_access('page_create', context, {})
            # TODO exceptions
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # saving a new page
        if request.POST and 'save_custom_page' in request.params and not data:
            try:
                check_access('page_create', context, {})
            except NotAuthorized:
                abort(401, _('Not authorized to see this page'))
            except Exception, e:
                error_summary = e.error_summary
                return self.error_message(error_summary)

            page_dict = self._populate_sections()

            try:
                get_action('page_create')(context, page_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new(page_dict, errors, error_summary)

        return base.render('pages/edit_page.html', extra_vars=extra_vars)

    def edit(self, id, data=None, errors=None, error_summary=None):

        context, extra_vars = self._init_data(data, error_summary, errors)

        try:
            check_access('page_update', context, {})
            # TODO exceptions
        except NotAuthorized:
            abort(401, _('Not authorized to edit this page'))

        # saving a new page
        if request.POST and 'save_custom_page' in request.params and not data:
            try:
                check_access('page_update', context, {})
            except NotAuthorized:
                abort(401, _('Not authorized to edit this page'))
            except Exception, e:
                error_summary = e.error_summary
                return self.error_message(error_summary)

            page_dict = self._populate_sections()
            try:
                get_action('page_update')(context, page_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.edit(page_dict, errors, error_summary)
            return base.render('pages/read_page.html')
        else:
            extra_vars['data'] = logic.get_action('page_show')(context, {'id': id})
            self._init_extra_vars_edit(extra_vars, id)

        return base.render('pages/edit_page.html', extra_vars=extra_vars)

    def read(self, id, type):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }
        page_dict = logic.get_action('page_show')(context, {'id': id})

        if page_dict.get('sections'):
            sections = json.loads(page_dict['sections'])
            page_dict['sections'] = sections

        vars = {
            'data': page_dict,
            'errors': {},
            'error_summary': {},
        }

        if not type or type != page_dict.get('type'):
            base.abort(404, _('Wrong page type'))
        else:
            return base.render('pages/read_page.html', extra_vars=vars)

    def _init_data(self, data, error_summary, errors):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        errors = errors or {}
        data_dict = {'content_type': [{'value': 'empty', 'text': _('Select content type')},
                                      {'value': 'map', 'text': _('Map')},
                                      {'value': 'key-figures', 'text': _('Key Figures')},
                                      {'value': 'interactive-data', 'text': _('Interactive Data')},
                                      {'value': 'data-list', 'text': _('Data List')}]}
        if data:
            data['sections'] = json.loads(data.get('sections', ''))
        extra_vars = {'data': data, 'data_dict': data_dict, 'errors': errors,
                      'error_summary': error_summary, 'action': 'new'}
        return context, extra_vars

    def _populate_sections(self):
        sections_no = int(request.params.get("hdx_counter") or "-1") + 1
        sections = []
        for _i in range(0, sections_no):
            if "field-section-" + str(_i) + "-type" in request.params:
                section = {
                    "type": request.params.get("field-section-" + str(_i) + "-type"),
                    "data-url": request.params.get("field-section-" + str(_i) + "-data-url"),
                    "section-title": request.params.get("field-section-" + str(_i) + "-section-title"),
                    "max-height": request.params.get("field-section-" + str(_i) + "-max-height"),
                    "description": request.params.get("field-section-" + str(_i) + "-section-description"),
                }
                sections.append(section)
        page_dict = {"name": request.params.get("name"), "title": request.params.get("title"),
                     "type": request.params.get("type"), "description": "", "sections": json.dumps(sections),
                     request.params.get("type"): checked, "hdx_counter": len(sections),
                     "id": request.params.get("hdx_page_id")}
        return page_dict

    def _init_extra_vars_edit(self, extra_vars, id):
        _data = extra_vars.get('data')
        _data['sections'] = json.loads(_data.get('sections', ''))
        _type = _data['type'] or 'crisis'
        _data[_type] = checked
        _data['hdx_counter'] = len(_data['sections'])
        _data['hdx_page_id'] = id
