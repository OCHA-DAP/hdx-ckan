import json
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

from ckanext.hdx_search.controllers.search_controller import HDXSearchController, get_default_facet_titles

from ckan.common import _, c, g, request, response
from ckan.controllers.api import CONTENT_TYPES
from urlparse import parse_qs, urlparse
import ckan.lib.navl.dictization_functions as dict_fns

tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
abort = base.abort
checked = 'checked="checked"'

# section_types = {
#     "empty": '',
#     "map": _('Map'),
#     "key_figures": _('Key Figures'),
#     "interactive_data": _('Interactive Data'),
#     "data_list": _('Data')
# }
section_types = {
    "empty": '',
    "map": _(''),
    "key_figures": _(''),
    "interactive_data": _(''),
    "data_list": _('')
}


class PagesController(HDXSearchController):
    def new(self, data=None, errors=None, error_summary=None):

        context, extra_vars = self._init_data(data, error_summary, errors)

        try:
            check_access('page_create', context, {})
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # checking pressed button
        active_page = request.params.get('save_custom_page')
        draft_page = request.params.get('save_as_draft_custom_page')
        state = active_page or draft_page

        # saving a new page
        if request.POST and state and not data:

            if state:
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
                mapped_action = self.generate_action_name(created_page.get("type"))
                h.redirect_to(mapped_action, id=created_page.get("name") or created_page.get("id"))

        return base.render('pages/edit_page.html', extra_vars=extra_vars)

    def generate_action_name(self, type):
        return 'read_event' if type == 'event' else 'read_dashboards'

    def edit(self, id, data=None, errors=None, error_summary=None):

        context, extra_vars = self._init_data(data, error_summary, errors)

        try:
            check_access('page_update', context, {})
        except NotAuthorized:
            abort(401, _('Not authorized to edit this page'))

        # checking pressed button
        active_page = request.params.get('save_custom_page')
        draft_page = request.params.get('save_as_draft_custom_page')
        delete_page = request.params.get('delete_custom_page')
        state = active_page or draft_page

        # saving a new page
        if request.POST and (state or delete_page) and not data:
            if state:
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
                mapped_action = self.generate_action_name(updated_page.get("type"))
                h.redirect_to(mapped_action, id=updated_page.get('name') or updated_page.get('id'))
            elif delete_page:
                h.redirect_to(controller='ckanext.hdx_pages.controllers.custom_page:PagesController', action='delete',
                              id=id)
        else:
            extra_vars['data'] = logic.get_action('page_show')(context, {'id': id})
            self._init_extra_vars_edit(extra_vars)

        return base.render('pages/edit_page.html', extra_vars=extra_vars)

    def read_event(self, id):
        return self.read_page(id, 'event')

    def read_dashboards(self, id):
        return self.read_page(id, 'dashboards')

    def read_page(self, id, type):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }

        try:
            page_dict = logic.get_action('page_show')(context, {'id': id})
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        if page_dict.get('sections'):
            sections = json.loads(page_dict['sections'])
            for section in sections:
                PagesController._compute_iframe_style(section)
                if section.get('type', '') == 'data_list':
                    saved_filters = PagesController._find_dataset_filters(section.get('data_url', ''))
                    c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)

                    # In case this is an AJAX request return JSON
                    if self._is_facet_only_request():
                        c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
                        response.headers['Content-Type'] = CONTENT_TYPES['json']
                        return json.dumps(c.full_facet_info)

            page_dict['sections'] = sections

            if len(sections) > 0 and sections[0].get('type', '') == 'map':
                page_dict['title_section'] = sections[0]
                del sections[0]

        vars = {
            'data': page_dict,
            'errors': {},
            'error_summary': {},
        }

        if not type or type != page_dict.get('type'):
            base.abort(404, _('Wrong page type'))
        else:
            return base.render('pages/read_page.html', extra_vars=vars)

    def delete(self, id):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }
        page_dict = logic.get_action('page_delete')(context, {'id': id})

        vars = {
            'data': page_dict,
            'errors': {},
            'error_summary': {},
        }
        # h.redirect_to('/')
        return base.render('home/index.html', extra_vars=vars)

    @staticmethod
    def _find_dataset_filters(url):
        filters = parse_qs(urlparse(url).query)
        return filters

    @staticmethod
    def _compute_iframe_style(section):
        style = 'width: 100%; '
        max_height = section.get('max_height')
        height = max_height if max_height else '400px'
        style += 'max-height: {}; '.format(max_height) if max_height else ''
        style += 'height: {}; '.format(height)
        section['style'] = style

    def _generate_dataset_results(self, page_id, type, saved_filters):

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        mapping_name = self.generate_action_name(type)

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            url = h.url_for(mapping_name, id=page_id, **params) + '#datasets-section'
            return url

        fq = ''
        search_params = {}
        for key, values_list in saved_filters.items():
            if key == 'q':
                fq = '"{}" {}'.format(values_list[0], fq)
            elif key in get_default_facet_titles().keys():
                for value in values_list:
                    fq += '%s:"%s" ' % (key, value)
            elif key == 'sort':
                search_params['default_sort_by'] = values_list[0]
            elif key == 'ext_page_size':
                search_params['num_of_items'] = values_list[0]

        search_params['additional_fq'] = fq

        package_type = 'dataset'
        full_facet_info = self._search(package_type, pager_url, **search_params)

        c.other_links['current_page_url'] = h.url_for(mapping_name, id=page_id)

        return full_facet_info

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
            data = {'event': checked, 'ongoing': checked, 'hdx_counter': 0}
        extra_vars = {'data': data, 'data_dict': data_dict, 'errors': errors,
                      'error_summary': error_summary, 'action': 'new'}
        return context, extra_vars

    def _populate_sections(self):
        sections_no = int(request.params.get("hdx_counter") or "0")
        sections = []

        data_dict_temp = clean_dict(dict_fns.unflatten(tuplize_dict(parse_params(request.POST))))

        for _i in range(0, sections_no):
            if "field_section_" + str(_i) + "_type" in request.params and request.params.get(
                                    "field_section_" + str(_i) + "_type") != 'empty':
                _title = self._get_default_title(request.params.get("field_section_" + str(_i) + "_type"),
                                                 request.params.get("field_section_" + str(_i) + "_section_title"))
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
        page_dict = {"name": request.params.get("name"),
                     "title": request.params.get("title"),
                     "type": request.params.get("type"),
                     "status": request.params.get("status"),
                     "description": "",
                     "sections": json.dumps(sections),
                     "groups": self.process_groups(data_dict_temp.get("groups", [])),
                     request.params.get("type") or 'event': checked,
                     request.params.get("status") or 'ongoing': checked,
                     "hdx_counter": len(sections),
                     "id": request.params.get("hdx_page_id"),
                     'state': request.params.get("save_custom_page") or request.params.get("save_as_draft_custom_page")}
        return page_dict

    def process_groups(self, groups):
        return groups if not isinstance(groups, basestring) else [groups]

    def _init_extra_vars_edit(self, extra_vars):

        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }

        _data = extra_vars.get('data')
        _data['sections'] = json.loads(_data.get('sections', ''))
        _data['groups'] = logic.get_action('page_group_list')(context, {'id': _data.get('id')})
        _type = _data['type'] or 'event'
        _data[_type] = checked
        _status = _data['status'] or 'ongoing'
        _data[_status] = checked
        _data['hdx_counter'] = len(_data['sections'])
        _data['hdx_page_id'] = _data.get('id')
        _data['mode'] = 'edit'

    def _get_default_title(self, type, title):
        if title is None or title == '':
            return section_types.get(type, '')
        return title
