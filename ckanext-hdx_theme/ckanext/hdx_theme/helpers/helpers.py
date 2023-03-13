import json
import datetime
import logging
import re
import six
import six.moves.urllib.parse as urlparse

import ckan.authz as new_authz
import ckan.lib.base as base
import ckan.lib.datapreview as datapreview
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.requestdata.model as requestdata_model
import ckanext.hdx_theme.version as version

from six import text_type

from ckan.lib import munge
from ckan.plugins import toolkit
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_FREQ_INFO
from ckanext.hdx_theme.util.light_redirect import switch_url_path

_ = toolkit._
request = toolkit.request
c = toolkit.c
config = toolkit.config
ungettext = toolkit.ungettext

log = logging.getLogger(__name__)

downloadable_formats = {
    'csv', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}


def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False


def is_not_zipped(res):
    url = res.get('url', 'zip').strip().lower()  # Default to zip so preview doesn't show if there is no url
    if re.search(r'zip$', url) or re.search(r'rar$', url):
        return False
    return True


NOT_HXL_FORMAT_LIST = ['zipped shapefile', 'zip', 'geojson', 'json', 'kml', 'kmz', 'rar', 'pdf', 'excel',
                       'zipped', 'docx', 'doc', '7z']


def _any(item, ext_list=NOT_HXL_FORMAT_LIST):
    return any(i in item for i in ext_list)


def is_not_hxl_format(res_format):
    if not res_format:
        return False
    return _any([res_format.lower()], NOT_HXL_FORMAT_LIST)


def get_facet_items_dict(facet, limit=1000, exclude_active=False):
    facets = h.get_facet_items_dict(
        facet, limit=limit, exclude_active=exclude_active)
    filtered_no_items = c.search_facets.get(facet)['items'].__len__()
    # total_no_items = json.loads(
    #     count.CountController.list[facet](count.CountController()))['count']
    # if filtered_no_items <= 50 and filtered_no_items < total_no_items:
    #     no_items = filtered_no_items
    # else:
    #     no_items = total_no_items
    no_items = filtered_no_items

    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return (facets[:limit], no_items)
    else:
        return (facets, no_items)


def get_last_modifier_user(dataset_id=None, group_id=None):
    if group_id is not None:
        activity_objects = model.activity.group_activity_list(group_id, limit=1, offset=0)
    if dataset_id:
        activity_objects = model.activity.package_activity_list(dataset_id, limit=1, offset=0)
    if activity_objects:
        user = activity_objects[0].user_id
        t_stamp = activity_objects[0].timestamp
        user_obj = model.User.get(user)
        return {"user_obj": user_obj, "last_modified": t_stamp.isoformat()}

    # in case there is no update date it will be displayed the current date
    return {"user_obj": None, "last_modified": None}


def get_filtered_params_list(params):
    result = []
    for (key, value) in params.items():
        if key not in {'q', 'sort'}:
            result.append((key, value))
    return result


# def get_last_revision_package(package_id):
#     #     pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
#     #     pkg = pkg_list[0]
#     #     return pkg.latest_related_revision.id
#     activity_objects = model.activity.package_activity_list(
#         package_id, limit=1, offset=0)
#     if len(activity_objects) > 0:
#         activity = activity_objects[0]
#         return activity.revision_id
#     return None


# def get_last_revision_group(group_id):
#     #     grp_list  = model.Session.query(model.Group).filter(model.Group.id == group_id).all()
#     #     grp = grp_list[0]
#     #     last_rev = grp.all_related_revisions[0][0]
#     activity_objects = model.activity.group_activity_list(
#         group_id, limit=1, offset=0)
#     if len(activity_objects) > 0:
#         activity = activity_objects[0]
#         return activity.revision_id
#     return None


def get_last_revision_timestamp_group(group_id):
    activity_objects = model.activity.group_activity_list(
        group_id, limit=1, offset=0)
    if len(activity_objects) > 0:
        activity = activity_objects[0]
        return h.render_datetime(activity.timestamp)
    return None


def get_dataset_date_format(date):
    # Is this a range?
    drange = date.split('-')
    if len(drange) != 2:
        drange = [date]
    dates = []
    for d in drange:
        try:
            dt = datetime.datetime.strptime(d, '%m/%d/%Y')
            dates.append(dt.strftime('%b %-d, %Y'))
        except:
            return False
    return '-'.join(dates)


def get_group_followers(grp_id):
    result = logic.get_action('group_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': grp_id})
    return result


def hdx_dataset_follower_count(pkg_id):
    result = logic.get_action('dataset_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': pkg_id})
    return result


def get_group_members(grp_id):
    member_list = logic.get_action('member_list')(
        {'model': model, 'session': model.Session},
        {'id': grp_id, 'object_type': 'user'})
    result = len(member_list)
    return result


def hdx_get_user_info(user_id):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    try:
        user = tk.get_action('hdx_basic_user_info')(context, {'id': user_id})
    except logic.NotAuthorized:
        base.abort(403, _('Unauthorized to see organization member list'))
    return user


def hdx_get_org_member_info(user_id, org_name=None):
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}

    if org_name:
        org_list = [{'name': org_name}]
    else:
        org_list = tk.get_action('hdx_organization_list_for_user')(context, {'id': user_id})

    user = tk.get_action('hdx_basic_user_info')(context, {'id': user_id})
    orgs_data = []

    for org in org_list:
        try:
            maint_pkgs = _get_packages_for_maintainer(context, user_id, org['name'])

            if maint_pkgs:
                org['pkgs'] = maint_pkgs
                orgs_data.append(org)
                user['maint_orgs_pkgs'] = orgs_data
        except logic.NotAuthorized:
            base.abort(403, _('Unauthorized to see organization member list'))
    return user


# HDX-8554 - org has to be organization name
def _get_packages_for_maintainer(context, id, org_name):
    result = logic.get_action('package_search')(context, {
        'q': '*:*',
        'fq': 'maintainer:{0}, organization:{1}'.format(id, org_name),
        'rows': 100,
    })
    return result['results']


def markdown_extract_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.markdown_extract(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result


def render_markdown_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.render_markdown(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result


def methodology_bk_compat(meth, other, render=True):
    if not meth and not other:
        return (None, None)
    standard_meths = ["Census", "Sample Survey",
                      "Direct Observational Data/Anecdotal Data", "Registry", "Other"]
    if meth in standard_meths and meth != "Other":
        if render:
            return (meth, None)
        else:
            return (meth, None)
    elif other:
        if render:
            return ("Other", h.render_markdown(other))
        else:
            return ("Other", other)
    else:
        meth = meth.split('Other - ')
        if render:
            return ("Other", h.render_markdown(meth[0]))
        else:
            return ("Other", meth[0])


def _hdx_strftime(_date):
    result = None
    try:
        result = _date.strftime('%B %d, %Y')
    except ValueError as e:
        month = datetime.date(1900, _date.month, 1).strftime('%B')
        result = month + " " + str(_date.day) + ", " + str(_date.year)
    return result


def render_date_from_concat_str(_str, separator='-'):
    result = ''
    if _str:
        if 'TO' in _str:
            res_list = []
            dates_list = str(_str).replace('[', '').replace(']', '').replace(' ', '').split('TO')
            for date in dates_list:
                if '*' not in date:
                    _date = datetime.datetime.strptime(date.split('T')[0], "%Y-%m-%d")
                    res_list.append(_hdx_strftime(_date))
                    # _date.strftime('%B %d, %Y'))
                else:
                    res_list.append(datetime.datetime.today().strftime('%B %d, %Y'))
            result = '-'.join(res_list)
        else:
            strdate_list = _str.split(separator)
            for index, strdate in enumerate(strdate_list):
                try:
                    date = datetime.datetime.strptime(strdate.strip(), '%m/%d/%Y')
                    render_strdate = date.strftime('%B %d, %Y')
                    result += render_strdate
                    if index < len(strdate_list) - 1:
                        result += ' - '
                except ValueError as e:
                    log.warning(e)

    return result


def hdx_build_nav_icon_with_message(menu_item, title, **kw):
    htmlResult = h.build_nav_icon(menu_item, title, **kw)
    if 'message' not in kw or not kw['message']:
        return htmlResult
    else:
        newResult = str(htmlResult).replace('</a>',
                                            ' <span class="nav-short-message">{message}</span></a>'.format(
                                                message=kw['message']))
        return h.literal(newResult)


def hdx_build_nav_no_icon(menu_item, title, **kw):
    html_result = str(h.build_nav_icon(menu_item, title, **kw))
    # print html_result
    start = html_result.find('<i ') - 1
    end = html_result.find('</i>') + 4
    if start > 0:
        new_result = html_result[0:start] + ' class="no-icon">' + html_result[end:]
    else:
        new_result = html_result
    # print new_result
    return h.literal(new_result)


def hdx_linked_user(user, maxlength=0):
    response = h.linked_user(user, maxlength)
    changed_response = re.sub(r"<img[^>]+/>", "", response)
    return h.literal(changed_response)


def hdx_show_singular_plural(num, singular_word, plural_word, show_number=True):
    response = None
    if num == 1:
        response = singular_word
    else:
        response = plural_word

    if show_number:
        return str(num) + ' ' + response
    else:
        return response


def hdx_num_of_new_related_items():
    max_days = 30
    count = 0
    now = datetime.datetime.now()
    for related in c.pkg.related:
        if (related.created):
            difference = now - related.created
            days = difference.days
            if days < max_days:
                count += 1
    return count


def hdx_user_count(only_sysadmin=False, include_site_user=False):
    site_id = config.get('ckan.site_id')
    q = model.Session.query(model.User).filter(model.User.state != 'deleted')
    if only_sysadmin:
        q = q.filter(model.User.sysadmin.is_(True))
    if not include_site_user:
        q = q.filter(model.User.name != site_id)
    return q.count()


def hdx_member_roles_list():
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author}
    return tk.get_action('member_roles_list')(context, {})


def hdx_version():
    ver = version.hdx_version
    if six.PY3:
        ver += ' PY3'
    return ver


def hdx_get_extras_element(data_dict, key='key', value_key='org_url', ret_key='value'):
    res = ''

    if value_key in data_dict:
        res = data_dict[value_key]
    else:
        extras = data_dict.get('extras', [])
        for ex in extras:
            if ex[key] == value_key:
                res = ex[ret_key]
    return res


def load_json(obj, **kw):
    return json.loads(obj, **kw)


def escaped_dump_json(obj, **kw):
    # escapes </ to prevent script tag hacking.
    return json.dumps(obj, **kw).replace('</', '<\\/')


def hdx_group_followee_list():
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj,
               'for_view': True}

    list = logic.get_action('group_followee_list')(
        context, {'id': c.userobj.id})
    # filter out the orgs
    groups = [group for group in list if not group['is_organization']]

    return groups


def hdx_organizations_available_with_roles():
    """
    Gets roles of organizations the current user belongs to
    """
    import ckanext.hdx_org_group.helpers.organization_helper as hdx_helper
    organizations_available = h.organizations_available('read', include_dataset_count=True)
    # if organizations_available and len(organizations_available) > 0:
    orgs_where_editor = []
    orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set([org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id'] for org in h.organizations_available('admin')])

    for org in organizations_available:
        org['has_add_dataset_rights'] = True
        if am_sysadmin:
            org['role'] = 'sysadmin'
        elif org['id'] in orgs_where_admin:
            org['role'] = 'admin'
        elif org['id'] in orgs_where_editor:
            org['role'] = 'editor'
        else:
            org['role'] = 'member'
            org['has_add_dataset_rights'] = False

    organizations_available.sort(key=lambda y: y['display_name'].lower())
    hdx_helper.org_add_last_updated_field(organizations_available)
    return organizations_available


def hdx_remove_schema_and_domain_from_url(url):
    urlTuple = urlparse.urlparse(url)
    if url.endswith('/preview'):
        # this is the case when the file needs to be transformed
        # before it can be previewed

        modifiedTuple = (('', '') + urlTuple[2:6])
    else:
        # this is for txt files
        # we force https since otherwise the browser will
        # anyway block loading mixed active content
        modifiedTuple = (('',) + urlTuple[1:6])
    modifiedUrl = urlparse.urlunparse(modifiedTuple)
    return modifiedUrl


def hdx_get_ckan_config(config_name):
    return config.get(config_name)


def get_group_name_from_list(glist, gid):
    for group in glist:
        if group['id'] == gid:
            return group['title']
    return ""


def hdx_follow_link(obj_type, obj_id, extra_text, cls=None, confirm_text=None):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return h.snippet('search/snippets/follow_link.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         extra_text=extra_text,
                         confirm_text=confirm_text,
                         cls=cls)
    return ''


def follow_status(obj_type, obj_id):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return following
    return False


def one_active_item(items):
    for i in items:
        if i['active']:
            return True
    return False


def feature_count(features):
    count = 0
    for name in features:
        facet = h.get_facet_items_dict(name)
        for f in facet:
            count += f['count']
    return count


def hdx_follow_button(obj_type, obj_id, **kw):
    ''' This is a modified version of the ckan core follow_button() helper
    It returns a simple link for a bootstrap dropdown menu

    Return a follow button for the given object type and id.

    If the user is not logged in return an empty string instead.

    :param obj_type: the type of the object to be followed when the follow
        button is clicked, e.g. 'user' or 'dataset'
    :type obj_type: string
    :param obj_id: the id of the object to be followed when the follow button
        is clicked
    :type obj_id: string

    :returns: a follow button as an HTML snippet
    :rtype: string

    '''
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        follow_extra_text = _('This Data')
        if kw and 'follow_extra_text' in kw:
            follow_extra_text = kw.pop('follow_extra_text')
        return h.snippet('snippets/hdx_follow_button.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         follow_extra_text=follow_extra_text,
                         params=kw)
    return ''


def hdx_add_url_param(alternative_url=None, controller=None, action=None,
                      extras=None, new_params=None, unwanted_keys=[]):
    '''
    MODIFIED CKAN HELPER THAT ALLOWS REMOVING SOME PARAMS

    Adds extra parameters to existing ones

    controller action & extras (dict) are used to create the base url
    via url_for(controller=controller, action=action, **extras)
    controller & action default to the current ones

    This can be overriden providing an alternative_url, which will be used
    instead.
    '''

    params_nopage = [(k, v) for k, v in request.params.items()
                     if k != 'page' and k not in unwanted_keys]
    params = set(params_nopage)
    if new_params:
        params |= set(new_params.items())
    if alternative_url:
        return h._url_with_params(alternative_url, params)
    return h._create_url_with_params(params=params, controller=controller,
                                     action=action, extras=extras)


def hdx_resource_preview(resource, package):
    ## COPY OF THE DEFAULT HELPER BY THE SAME NAME BUT FORCES URLS OVER HTTPS
    '''
    Returns a rendered snippet for a embedded resource preview.

    Depending on the type, different previews are loadeSd.
    This could be an img tag where the image is loaded directly or an iframe
    that embeds a web page, recline or a pdf preview.
    '''

    if not resource['url']:
        return False

    format_lower = datapreview.res_format(resource)
    directly = False
    data_dict = {'resource': resource, 'package': package}

    if datapreview.get_preview_plugin(data_dict, return_first=True):
        url = tk.url_for(controller='package', action='resource_datapreview',
                         resource_id=resource['id'], id=package['id'], qualified=True)
    else:
        return False

    return h.snippet("dataviewer/snippets/data_preview.html",
                     embed=directly,
                     resource_url=url,
                     raw_resource_url=https_load(resource.get('url')))


def https_load(url):
    return re.sub(r'^http://', '//', url)


def count_public_datasets_for_group(datasets_list):
    a = len([i for i in datasets_list if i['private'] == False])
    return a


def check_all_str_fields_not_empty(dictionary, warning_template, skipped_keys=[], errors=None):
    for key, value in dictionary.items():
        if key not in skipped_keys:
            value = value.strip() if value else value
            if not value:
                message = warning_template.format(key)
                log.warning(message)
                add_error('Empty field', message, errors)
                return False
    return True


def add_error(type, message, errors):
    if isinstance(errors, list):
        errors.append({'_type': type, 'message': message})


def hdx_popular(type_, number, min=1, title=None):
    ''' display a popular icon. '''
    from ckan.lib.helpers import snippet as snippet
    if type_ == 'views':
        title = ungettext('{number} view', '{number} views', number)
    elif type_ == 'recent views':
        title = ungettext('{number} recent view', '{number} recent views', number)
    elif type_ == 'downloads':
        title = ungettext('{number} download', '{number} downloads', number)
    elif not title:
        raise Exception('popular() did not recieve a valid type_ or title')
    return snippet('snippets/popular.html', title=title, number=number, min=min)


def hdx_license_list():
    license_touple_list = base.model.Package.get_license_options()
    license_dict_list = [{'value': _id, 'text': _title} for _title, _id in license_touple_list]
    return license_dict_list


def hdx_methodology_list():
    result = [{'value': '-1', 'text': '-- Please select --'}, {'value': 'Census', 'text': 'Census'},
              {'value': 'Sample Survey', 'text': 'Sample Survey'},
              {'value': 'Direct Observational Data/Anecdotal Data', 'text': 'Direct Observational Data/Anecdotal Data'},
              {'value': 'Registry', 'text': 'Registry'}, {'value': 'Other', 'text': 'Other'}]
    return result


def hdx_location_list(include_world=True):
    top_values = []
    if include_world:
        top_values.append('world')

    top_locations = []
    bottom_locations = []

    locations = logic.get_action('cached_group_list')({}, {})
    for loc in locations:
        location_data = {'value': loc.get('name'), 'text': loc.get('title')}
        if loc.get('name') in top_values:
            top_locations.append(location_data)
        else:
            bottom_locations.append(location_data)

    return top_locations + bottom_locations


def hdx_organisation_list():
    orgs = h.organizations_available('create_dataset')
    orgs_dict_list = [{'value': org.get('name'), 'text': org.get('title')} for org in orgs]
    return orgs_dict_list


def hdx_tag_list():
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        tags = logic.get_action('tag_list')(context, {})
        tags_dict_list = [{'value': tag, 'text': tag} for tag in tags]
        return tags_dict_list
    return []


def hdx_dataset_preview_values_list():
    import ckanext.hdx_package.helpers.custom_validator as vd
    result = [{'value': vd._DATASET_PREVIEW_FIRST_RESOURCE, 'text': 'Default (first resource with preview)'}]
    return result


def hdx_frequency_list(for_sysadmin=False, include_value=None):
    result = [
        {'value': key, 'text': val['title'], 'onlySysadmin': False}
        for key, val in UPDATE_FREQ_INFO.items()
    ]
    result.insert(0, {'value': '-999', 'text': '-- Please select --', 'onlySysadmin': False})

    filtered_result = result
    if not for_sysadmin:
        filtered_result = [r for r in result if not r.get('onlySysadmin') or include_value == r.get('value')]

    return filtered_result


def hdx_get_frequency_by_value(value):
    return UPDATE_FREQ_INFO.get(value, {}).get('title', '')


# def hdx_get_layer_info(id=None):
#     layer = explorer.explorer_data.get(id)
#     return layer


def hdx_get_carousel_list():
    return logic.get_action('hdx_carousel_settings_show')({}, {})


def hdx_get_quick_links_list():
    return logic.get_action('hdx_quick_links_settings_show')({}, {})


def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': c.user or c.author,
        'auth_user_obj': c.userobj
    }


def _get_action(action, data_dict):
    return toolkit.get_action(action)(_get_context(), data_dict)


def hdx_is_current_user_a_maintainer(maintainers, pkg):
    if c.user:
        current_user = _get_action('user_show', {'id': c.user})
        user_id = current_user.get('id')
        user_name = current_user.get('name')

        if maintainers and (user_id in maintainers or user_name in maintainers):
            return True

    return False


def hdx_is_sysadmin(user_id):
    import ckan.authz as authz
    user_obj = model.User.get(user_id)
    if not user_obj:
        return False
        # raise logic.NotFound
    user = user_obj.name
    return authz.is_sysadmin(user)


def hdx_organization_list_for_user(user_id):
    orgs = []
    if user_id:
        # context = {
        #     'model': model,
        #     'session': model.Session,
        # }
        # user = model.User.get(user_id)
        # if user:
        #     context['auth_user_obj'] = user
        #     context['user'] = user.name
        # return tk.get_action('organization_list_for_user')(context, {'id': user_id})
        return tk.get_action('hdx_organization_list_for_user')(_get_context(), {'id': user_id})
    return orgs


def hdx_dataset_is_hxl(tag_list):
    for tag in tag_list:
        if tag.get('name') == 'hxl' and tag.get('display_name') == 'hxl':
            return True
    return False


def hdx_dataset_has_sadd(tag_list):
    for tag in tag_list:
        if tag.get('name') == 'sex and age disaggregated data - sadd' and tag.get(
            'display_name') == 'sex and age disaggregated data - sadd':
            return True
    return False


def hdx_switch_url_path():
    return switch_url_path()


def hdx_munge_title(title):
    return munge.munge_title_to_name(title)


def hdx_check_http_response(response_code, comparison_http_code):
    '''
    :param response_code: code generated by the python APP (can come from flask or pylons in different types)
    :type response_code: Union[int, str, list]
    :param comparison_http_code: what we're comparing against
    :type comparison_http_code: int

    :returns: whether the response_code matches the comparison_http_code
    :rtype: bool
    '''
    try:
        if response_code == comparison_http_code:
            return True
        elif response_code == str(comparison_http_code):
            return True
        elif response_code[0] == comparison_http_code:
            return True
    except TypeError as e:
        log.info('Follwing error was generated from hdx_check_http_response():' + text_type(e))
    return False


def hdx_get_request_param(param_name, default_value):
    '''
    This should get the request param value whether we're in pylons or flask
    '''
    try:
        value = request.args.get(param_name)
    except Exception as e:
        log.warning('Error when looking into "args" of request. This could be normal in a pylons request: '
                    + text_type(e))
        value = request.params.get(param_name)

    value = default_value if value is None else value
    return value


def hdx_url_for(*args, **kw):
    '''
    Removes the '/' at the end of an URL returned by the core CKAN url_for() helper.
    It appears when url_for() thinks it can return a flask route. But if it's a pylons
    controller that needs to render the page the '/' gets in the way.
    '''

    # If the html template calls this with both named route and controller + action, just use named route
    if len(args) > 0 and args[0]:
        kw.pop('controller', None)
        kw.pop('action', None)
    else:
        args = []

    url = tk.url_for(*args, **kw)
    if url and len(url) > 1:
        if url.endswith('/'):
            url = url[:-1]
        elif '/?' in url:
            url = url.replace('/?', '?')
    return url


url_for = hdx_url_for


def hdx_pending_request_data(user_id, package_id):
    return requestdata_model.ckanextRequestdata.get_pending_request(package_id, user_id, ['new', 'open'])
