import json
import logging

import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import _, config, g, request
from flask import Blueprint
from flask.views import MethodView
from six import string_types

import ckanext.hdx_pages.helpers.helper as page_h
import ckanext.hdx_search.cli.click_feature_search_command as lunr

# import ckanext.hdx_package.helpers.helpers as pkg_h
# if not six.PY3:
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

# else:
#     @decorator
#     def check_redirect_needed(original_action, *args, **kw):
#         return original_action(*args, **kw)

tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params
get_action = logic.get_action
check_access = logic.check_access
render = tk.render
abort = tk.abort
log = logging.getLogger(__name__)
checked = 'checked="checked"'

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

section_types = {
    "empty": "",
    "description": "",
    "map": "",
    "key_figures": "",
    "interactive_data": "",
    "data_list": "",
}

# Blueprints definitions
hdx_light_event = Blueprint("hdx_light_event", __name__, url_prefix="/m/event")
hdx_light_dashboard = Blueprint(
    "hdx_light_dashboard", __name__, url_prefix="/m/dashboards"
)

hdx_event = Blueprint("hdx_event", __name__, url_prefix="/event")
hdx_dashboard = Blueprint("hdx_dashboard", __name__, url_prefix="/dashboards")

hdx_custom_page = Blueprint("hdx_custom_page", __name__, url_prefix="/page")


@check_redirect_needed
def read_light_event(id):
    return _read(id, True, False)


@check_redirect_needed
def read_light_dashboard(id):
    return _read(id, True, False)


@check_redirect_needed
def read_event(id):
    return _read(id, False, True)


@check_redirect_needed
def read_dashboard(id):
    return _read(id, False, True)


def _update_lunr():
    test = True if config.get("ckan.site_id") == "test.ckan.net" else False
    if not test:
        lunr.build_index()


# def delete_page(id):
#     context = {
#         u'model': model,
#         u'session': model.Session,
#         u'user': g.user,
#         u'auth_user_obj': g.userobj,
#     }
#     try:
#         check_access('page_delete', context, {})
#     except NotAuthorized:
#         abort(404, _('Page not found'))
#
#     try:
#         page_dict = logic.get_action('page_delete')(context, {'id': id})
#     except NotFound:
#         abort(404, _('Page not found'))
#     except Exception as ex:
#         abort(404, _('Page not found'))
#     _update_lunr()
#
#     vars = {
#         'data': page_dict,
#         'errors': {},
#         'error_summary': {},
#     }
#     url = h.url_for('hdx_custom_pages.index')
#     return h.redirect_to(url)
# return render('home/index.html', vars)


def _populate_template_data(page_dict, show_switch_to_mobile):
    from ckanext.hdx_pages.controller_logic.custom_pages_search_logic import (
        CustomPagesSearchLogic,
    )

    if page_dict.get("sections"):
        sections = json.loads(page_dict["sections"])
        for section in sections:
            page_h._compute_iframe_style(section, is_mobile=True)
            if section.get("type", "") == "data_list":
                saved_filters = page_h._find_dataset_filters(
                    section.get("data_url", "")
                )

                cp_search_logic = CustomPagesSearchLogic(
                    page_dict.get("name"), page_dict.get("type")
                )
                search_params = page_h.generate_dataset_results(
                    page_dict.get("id"), page_dict.get("type"), saved_filters
                )
                cp_search_logic._search(**search_params)
                archived_url_helper = cp_search_logic.add_archived_url_helper()
                redirect_result = archived_url_helper.redirect_if_needed()
                if redirect_result:
                    return redirect_result

                section["template_data"] = cp_search_logic.template_data
                log.info(saved_filters)
                # c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
            #
            #     # In case this is an AJAX request return JSON
            #     if self._is_facet_only_request():
            #         c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
            #         response.headers['Content-Type'] = CONTENT_TYPES['json']
            #         return json.dumps(c.full_facet_info)

        page_dict["sections"] = sections

        if (
            show_switch_to_mobile
            and len(sections) > 0
            and sections[0].get("type", "") == "map"
        ):
            page_dict["title_section"] = sections[0]
            del sections[0]
    return None


def _read(id, show_switch_to_desktop, show_switch_to_mobile):
    try:
        context = {
            "model": model,
            "session": model.Session,
            "user": g.user,
            "auth_user_obj": g.userobj,
            "for_view": True,
        }
        check_access("site_read", context)
    except NotAuthorized:
        abort(403, _("Not authorized to see this page"))

    page_dict = None
    try:
        page_dict = get_action("page_show")(context, {"id": id})
    except NotAuthorized:
        abort(404, _("Page not found"))
    except NotFound:
        abort(404, _("Page not found"))

    redirect_needed = _populate_template_data(page_dict, show_switch_to_mobile)
    if redirect_needed:
        return redirect_needed
    template_data = {
        "page_dict": page_dict,
        "page_has_desktop_version": show_switch_to_desktop,
        "page_has_mobile_version": show_switch_to_mobile,
    }

    if show_switch_to_mobile:
        return render("pages/read_page.html", template_data)
    return render("light/custom_pages/read.html", template_data)


# helper functions
def _init_data(data, error_summary, errors):
    context = {
        "model": model,
        "session": model.Session,
        "user": g.user,
        "auth_user_obj": g.userobj,
    }
    errors = errors or {}
    data_dict = {
        "content_type": [
            {"value": "empty", "text": _("Select content type")},
            {"value": "description", "text": _("Description/Text")},
            {"value": "map", "text": _("Map")},
            {"value": "key_figures", "text": _("Key Figures")},
            {"value": "interactive_data", "text": _("Interactive Data")},
            {"value": "data_list", "text": _("Data List")},
        ]
    }
    if data:
        data["sections"] = json.loads(data.get("sections", ""))
    else:
        data = {"event": checked, "ongoing": checked, "hdx_counter": 0}
    extra_vars = {
        "data": data,
        "data_dict": data_dict,
        "errors": errors,
        "error_summary": error_summary,
        "action": "new",
    }
    return context, extra_vars


def _get_default_title(type, title):
    if title is None or title == "":
        return section_types.get(type, "")
    return title


def _populate_sections():
    sections_no = int(request.form.get("hdx_counter") or "0")
    sections = []

    data_dict_temp = clean_dict(
        dict_fns.unflatten(tuplize_dict(parse_params(request.form)))
    )

    for _i in range(0, sections_no):
        if (
            "field_section_" + str(_i) + "_type" in request.form
            and request.form.get("field_section_" + str(_i) + "_type")
            != "empty"
        ):
            _title = _get_default_title(
                request.form.get("field_section_" + str(_i) + "_type"),
                request.form.get(
                    "field_section_" + str(_i) + "_section_title"
                ),
            )
            size = request.form.get("field_section_" + str(_i) + "_max_height")
            m_size = request.form.get(
                "field_section_" + str(_i) + "_m_max_height"
            )
            # if size and size == '':
            #     size = '400px'
            section = {
                "type": request.form.get("field_section_" + str(_i) + "_type"),
                "data_url": request.form.get(
                    "field_section_" + str(_i) + "_data_url"
                ),
                "section_title": _title,
                "max_height": size,
                "m_max_height": m_size,
                "description": request.form.get(
                    "field_section_" + str(_i) + "_section_description"
                ),
                "long_description": request.form.get(
                    "field_section_" + str(_i) + "_section_long_description"
                ),
            }
            sections.append(section)

    page_dict = {
        "name": request.form.get("name"),
        "title": request.form.get("title"),
        "type": request.form.get("type"),
        "status": request.form.get("status"),
        "description": request.form.get("description"),
        "extras": json.dumps(
            {"show_title": request.form.get("show_title", "off")}
        ),
        "sections": json.dumps(sections),
        "groups": _process_groups(data_dict_temp.get("groups", [])),
        "tags": _process_tags(data_dict_temp.get("tag_string", "")),
        "tag_string": data_dict_temp.get("tag_string", ""),
        request.form.get("type") or "event": checked,
        request.form.get("status") or "ongoing": checked,
        "hdx_counter": len(sections),
        "id": request.form.get("id"),
        "state": request.form.get("save_custom_page")
        or request.form.get("save_as_draft_custom_page"),
    }
    return page_dict


def _process_groups(groups):
    return groups if not isinstance(groups, string_types) else [groups]


def _process_tags(tag_string):
    tag_list = []
    for tag in tag_string.split(","):
        tag = tag.strip().lower()
        if tag:
            tag_list.append({"name": tag, "state": "active"})
    # result = pkg_h.get_tag_vocabulary(tag_list)
    return tag_list


def _generate_action_name(_type):
    if _type == "event":
        return "hdx_event.read_event"
    if _type == "dashboard":
        return "hdx_dashboard.read_dashboard"
    return "hdx_event.read_event"


def _init_extra_vars_edit(extra_vars):
    context = {
        "model": model,
        "session": model.Session,
        "user": g.user,
        "auth_user_obj": g.userobj,
    }

    _data = extra_vars.get("data")
    _data["sections"] = json.loads(_data.get("sections", ""))
    _data["groups"] = logic.get_action("page_group_list")(
        context, {"id": _data.get("id")}
    )
    _type = _data["type"] or "event"
    _data[_type] = checked
    _status = _data["status"] or "ongoing"
    _data[_status] = checked
    _data["hdx_counter"] = len(_data["sections"])
    _data["description"] = _data.get("description")
    _data["extras"] = _data.get("extras") or json.loads('{"show_title": "on"}')


# Class definitions
class CreateView(MethodView):
    def post(self, data=None, errors=None, error_summary=None):
        # ckan_phase = request.form.get(u'_ckan_phase')
        context, extra_vars = _init_data(data, error_summary, errors)
        try:
            check_access("page_create", context, {})
        except NotAuthorized:
            abort(404, _("Page not found"))
        except Exception as ex:
            log.error(ex)

        # checking pressed button
        active_page = request.form.get("save_custom_page")
        draft_page = request.form.get("save_as_draft_custom_page")
        state = active_page or draft_page

        # saving a new page
        if state and not data:
            page_dict = _populate_sections()
            try:
                created_page = get_action("page_create")(context, page_dict)
                _update_lunr()
            except logic.ValidationError as e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.post(page_dict, errors, error_summary)

            _blueprint = _generate_action_name(created_page.get("type"))

            return h.redirect_to(_blueprint, id=created_page.get("name"))

        return render("pages/edit_page.html", extra_vars=extra_vars)

    def get(self, data=None, errors=None, error_summary=None):
        context, extra_vars = _init_data(data, error_summary, errors)
        try:
            check_access("page_create", context, {})
        except NotAuthorized:
            abort(404, _("Page not found"))

        return render("pages/edit_page.html", extra_vars=extra_vars)


class EditView(MethodView):
    def post(self, id, data=None, errors=None, error_summary=None):
        context, extra_vars = _init_data(data, error_summary, errors)

        try:
            check_access("page_update", context, {})
        except NotAuthorized:
            abort(404, _("Page not found"))
        except Exception as ex:
            log.error(ex)

        # checking pressed button
        active_page = request.form.get("save_custom_page")
        draft_page = request.form.get("save_as_draft_custom_page")
        state = active_page or draft_page

        # saving a new page
        if state and not errors:
            page_dict = _populate_sections()
            page_dict["id"] = id
            try:
                updated_page = get_action("page_update")(context, page_dict)
                _update_lunr()
            except logic.ValidationError as e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.post(id, page_dict, errors, error_summary)

            _blueprint = _generate_action_name(updated_page.get("type"))

            return h.redirect_to(_blueprint, id=updated_page.get("id"))

        return render("pages/edit_page.html", extra_vars=extra_vars)

    def get(self, id, data=None, errors=None, error_summary=None):
        context, extra_vars = _init_data(data, error_summary, errors)

        try:
            check_access("page_update", context, {})
        except NotAuthorized:
            abort(404, _("Page not found"))

        try:
            extra_vars["data"] = logic.get_action("page_show")(
                context, {"id": id}
            )
            extra_vars["data"]["tag_string"] = ", ".join(
                h.dict_list_reduce(extra_vars["data"].get("tags", {}), "name")
            )
            _init_extra_vars_edit(extra_vars)

            return render("pages/edit_page.html", extra_vars=extra_vars)
        except NotFound:
            abort(404, _("Page not found"))


class DeleteView(MethodView):
    def post(self, id, data=None, errors=None, error_summary=None):
        context = {
            "model": model,
            "session": model.Session,
            "user": g.user,
            "auth_user_obj": g.userobj,
        }
        try:
            check_access("page_delete", context, {})
        except NotAuthorized:
            abort(404, _("Page not found"))
        try:
            logic.get_action("page_delete")(context, {"id": id})
        except NotFound:
            abort(404, _("Page not found"))
        except Exception:
            abort(404, _("Page not found"))
        _update_lunr()

        # vars = {
        #     'data': page_dict,
        #     'errors': {},
        #     'error_summary': {},
        # }
        url = h.url_for("hdx_custom_pages.index")
        return h.redirect_to(url)

    # def get(self, id, data=None, errors=None, error_summary=None):
    #     context, extra_vars = _init_data(data, error_summary, errors)
    #
    #     try:
    #         check_access('page_update', context, {})
    #     except NotAuthorized:
    #         abort(404, _('Page not found'))
    #
    #     extra_vars['data'] = logic.get_action('page_show')(context, {'id': id})
    #     extra_vars['data']['tag_string'] = ', '.join(h.dict_list_reduce(extra_vars['data'].get('tags', {}), 'name'))
    #     _init_extra_vars_edit(extra_vars)
    #
    #     return render('pages/edit_page.html', extra_vars=extra_vars)


# Rules definitions
hdx_light_event.add_url_rule(
    "/<id>/", view_func=read_light_event, strict_slashes=False
)
hdx_light_dashboard.add_url_rule(
    "/<id>/", view_func=read_light_dashboard, strict_slashes=False
)

hdx_event.add_url_rule("/<id>/", view_func=read_event, strict_slashes=False)
hdx_dashboard.add_url_rule(
    "/<id>/", view_func=read_dashboard, strict_slashes=False
)

hdx_custom_page.add_url_rule("/new", view_func=CreateView.as_view(str("new")))
hdx_custom_page.add_url_rule(
    "/edit/<id>", view_func=EditView.as_view(str("edit"))
)
hdx_custom_page.add_url_rule(
    "/delete/<id>", view_func=DeleteView.as_view(str("delete_page"))
)
