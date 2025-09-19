import logging
import json
from flask import Blueprint

import ckan.common as common
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_package.helpers.analytics as analytics

from ckan.views.group import CreateGroupView

from ckanext.hdx_org_group.controller_logic.group_read_logic import GroupIndexReadLogic, GroupReadLogic
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed
from ckanext.hdx_users.general_token_model import ObjectType
from ckanext.hdx_users.helpers.notification_platform import add_unsubscribe_token

g = common.g
request = common.request
render = tk.render
redirect = tk.redirect_to
url_for = tk.url_for
get_action = tk.get_action
NotFound = tk.ObjectNotFound
check_access = tk.check_access
NotAuthorized = tk.NotAuthorized
abort = tk.abort
_ = tk._

log = logging.getLogger(__name__)

GROUP_TYPES = ['group']

hdx_group = Blueprint(u'hdx_group', __name__, url_prefix=u'/group')
# hdx_country_topline = Blueprint(u'hdx_country_topline', __name__, url_prefix=u'/country')


def index():
    return _index('light/group/index.html', False, False)


def _index(template_file, show_switch_to_desktop, show_switch_to_mobile):
    user = g.user
    index_read_logic = GroupIndexReadLogic(user)
    index_read_logic.read()
    countries = json.dumps(index_read_logic.all_countries_world_1st)
    template_data = {
        'countries': countries,
        'page_has_desktop_version': show_switch_to_desktop,
        'page_has_mobile_version': show_switch_to_mobile,
    }
    return render(template_file, template_data)


# def country_topline(id):
#     log.info("The id of the page is: " + id)
#
#     topline_read_logic = CountryToplineReadLogic(id).read()
#
#     return render('country/country_topline.html', extra_vars=topline_read_logic.template_data)


@check_redirect_needed
def read(id):
    return _read('country/country.html', id, False, True)


def _read(template_file, id, show_switch_to_desktop, show_switch_to_mobile):
    context = {
        'model': model,
        'session': model.Session,
        'for_view': True,
        'with_private': False
    }
    if id == 'ebola':
        return redirect(url_for('hdx_ebola.read'))

    group_read_logic = GroupReadLogic(group_id=id).read()
    if group_read_logic.redirect_result:
        return group_read_logic.redirect_result
    else:
        template_data = group_read_logic.widgets_data
        template_data['analytics'] = {
            'analytics_came_from': analytics.came_from(request.args),
            'analytics_supports_notifications': analytics.supports_notifications(ObjectType.GROUP,
                                                                                 group_read_logic.country_dict),
        }
        unsubscribe_token = request.args.get('_unsubscribe_token', None)
        add_unsubscribe_token(unsubscribe_token, ObjectType.GROUP, group_read_logic.country_dict.get('id'), template_data)
        return render(template_file, template_data)


hdx_group.add_url_rule(u'/', view_func=index, strict_slashes=False)
hdx_group.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateGroupView.as_view(str(u'new')),
        defaults={
            'group_type': 'group',
            'is_organization': False
        }
)
hdx_group.add_url_rule(u'/<id>', view_func=read)

# hdx_country_topline.add_url_rule(u'/topline/<id>', view_func=country_topline)
