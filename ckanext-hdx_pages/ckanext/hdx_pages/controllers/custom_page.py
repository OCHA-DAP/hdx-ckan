import json
import ckan.lib.base as base
from ckan.common import _, c, g, request, response
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
abort = base.abort

checked = 'checked="checked"'

section_types = {
    "empty": '',
    "map": _('Map'),
    "key_figures": _('Key Figures'),
    "interactive_data": _('Interactive Data'),
    "data_list": _('Data')
}


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
                created_page = get_action('page_create')(context, page_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new(page_dict, errors, error_summary)
            h.redirect_to(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='read',
                          id=created_page.get("name") or created_page.get("id"), type=created_page.get("type"))

        return base.render('pages/edit_page.html', extra_vars=extra_vars)

    def edit(self, id, data=None, errors=None, error_summary=None):

        context, extra_vars = self._init_data(data, error_summary, errors)

        try:
            check_access('page_update', context, {})
            # TODO exceptions
        except NotAuthorized:
            abort(401, _('Not authorized to edit this page'))

        # checking pressed button
        active_page = request.params.get('save_custom_page')
        draft_page = request.params.get('save_as_draft_custom_page')
        state = active_page or draft_page

        # saving a new page
        if request.POST and state and not data:
            try:
                check_access('page_update', context, {})
            except NotAuthorized:
                abort(401, _('Not authorized to edit this page'))
            except Exception, e:
                error_summary = e.error_summary
                return self.error_message(error_summary)

            page_dict = self._populate_sections()
            try:
                updated_page = get_action('page_update')(context, page_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.edit(id, page_dict, errors, error_summary)
            h.redirect_to(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='read',
                          id=updated_page.get('name') or updated_page.get('id'), type=updated_page.get('type'))
        else:
            extra_vars['data'] = logic.get_action('page_show')(context, {'id': id})
            self._init_extra_vars_edit(extra_vars)

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

    def _init_data(self, data, error_summary, errors, id=None):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        errors = errors or {}
        data_dict = {'content_type': [{'value': 'empty', 'text': _('Select content type')},
                                      {'value': 'map', 'text': _('Map')},
                                      {'value': 'key_figures', 'text': _('Key Figures')},
                                      {'value': 'interactive_data', 'text': _('Interactive Data')},
                                      {'value': 'data_list', 'text': _('Data List')}]}
        if data:
            data['sections'] = json.loads(data.get('sections', ''))
        else:
            data = {'crisis': checked, 'hdx_counter': 0}
        extra_vars = {'data': data, 'data_dict': data_dict, 'errors': errors,
                      'error_summary': error_summary, 'action': 'new'}
        return context, extra_vars

    def _populate_sections(self):
        sections_no = int(request.params.get("hdx_counter") or "0")
        sections = []
        for _i in range(0, sections_no):
            if "field_section_" + str(_i) + "_type" in request.params and request.params.get("field_section_" + str(_i) + "_type") != 'empty':
                _title = self._get_default_title(request.params.get("field_section_" + str(_i) + "_type"), request.params.get("field_section_" + str(_i) + "_section_title"))
                size = request.params.get("field_section_" + str(_i) + "_max_height")
                # if size and size == '':
                #     size = '400px'
                section = {
                    "type": request.params.get("field_section_" + str(_i) + "_type"),
                    "data_url": request.params.get("field_section_" + str(_i) + "_data_url"),
                    "section_title": _title,
                    "max_height": size,
                    "description": request.params.get("field_section_" + str(_i) + "_section_description"),
                }
                sections.append(section)
        page_dict = {"name": request.params.get("name"), "title": request.params.get("title"),
                     "type": request.params.get("type"), "description": "", "sections": json.dumps(sections),
                     request.params.get("type") or 'crisis': checked, "hdx_counter": len(sections),
                     "id": request.params.get("hdx_page_id"),
                     'state': request.params.get("save_custom_page") or request.params.get("save_as_draft_custom_page")}
        return page_dict

    def _init_extra_vars_edit(self, extra_vars):
        _data = extra_vars.get('data')
        _data['sections'] = json.loads(_data.get('sections', ''))
        _type = _data['type'] or 'crisis'
        _data[_type] = checked
        _data['hdx_counter'] = len(_data['sections'])
        _data['hdx_page_id'] = _data.get('id')

    def _get_default_title(self, type, title):
        if title is None or title == '':
            return section_types.get(type, '')
        return ''
