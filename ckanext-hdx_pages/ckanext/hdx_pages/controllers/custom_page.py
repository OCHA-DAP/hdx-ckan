import json
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

from ckanext.hdx_search.controllers.search_controller import HDXSearchController, get_default_facet_titles

from ckan.common import _, c, g, request, response
from ckan.controllers.api import CONTENT_TYPES
from urlparse import parse_qs, urlparse

get_action = logic.get_action
check_access = logic.check_access
NotAuthorized = logic.NotAuthorized
abort = base.abort

checked = 'checked="checked"'


class PagesController(HDXSearchController):
    def new(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        try:
            check_access('page_create', context, {})
            # TODO exceptions
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        errors = errors or {}
        data_dict = {'content_type': [{'value': 'empty', 'text': _('Select content type')},
                                      {'value': 'map', 'text': _('Map')},
                                      {'value': 'key-figures', 'text': _('Key Figures')},
                                      {'value': 'interactive-data', 'text': _('Interactive Data')},
                                      {'value': 'data-list', 'text': _('Data List')}]}
        vars = {'data': data, 'data_dict': data_dict, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}

        # saving a new page
        if request.POST and 'save_custom_page' in request.params and not data:

            try:
                check_access('page_create', context, {})
                # TODO exceptions
            except NotAuthorized:
                abort(401, _('Not authorized to see this page'))
            except Exception, e:
                error_summary = e.error_summary
                return self.error_message(error_summary)
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
                         request.params.get("type"): checked}
            try:
                get_action('page_create')(context, page_dict)
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.new(page_dict, errors, error_summary)

        return base.render('pages/edit_page.html', extra_vars=vars)

    def edit(self, id):
        return None

    def read(self, id, type):
        context = {
            'model': model, 'session': model.Session,
            'user': c.user or c.author
        }
        page_dict = logic.get_action('page_show')(context, {'id': id})

        if page_dict.get('sections'):
            sections = json.loads(page_dict['sections'])
            for section in sections:
                PagesController._compute_iframe_style(section)
                if section.get('type', '') == 'data-list':
                    saved_filters = PagesController._find_dataset_filters(section.get('data-url', ''))
                    c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)

                    # In case this is an AJAX request return JSON
                    if self._is_facet_only_request():
                        c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
                        response.headers['Content-Type'] = CONTENT_TYPES['json']
                        return json.dumps(c.full_facet_info)
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

    @staticmethod
    def _find_dataset_filters(url):
        filters = parse_qs(urlparse(url).query)
        return filters

    @staticmethod
    def _compute_iframe_style(section):
        style = 'width: 100%; '
        max_height = section.get('max-height')
        height = max_height if max_height else '400px'
        style += 'max-height: {}; '.format(max_height) if max_height else ''
        style += 'height: {}; '.format(height)
        section['style'] = style

    def _generate_dataset_results(self, page_id, type, saved_filters):

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            url = h.url_for('read_page', id=page_id, type=type, **params) + '#datasets-section'
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

        c.other_links['current_page_url'] = h.url_for('read_page', id=page_id, type=type)

        return full_facet_info
