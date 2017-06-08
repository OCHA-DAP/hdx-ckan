import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import pylons.config as config

_check_access = logic.check_access
NotFound = logic.NotFound
get_action = logic.get_action
NoOfLocs = 5
NoOfOrgs = 5
c_nepal_earthquake = config.get('hdx.crisis.nepal_earthquake')



@logic.side_effect_free
def onboarding_followee_list(context, data_dict):
    # TODO check if user is following org&locs
    result = []

    # data_filter = {'package_count': True, 'include_extras': True, 'all_fields': True, 'sort': 'package_count desc'}

    locs = get_action('cached_group_list')(context, {})
    locs = sorted(locs, key=lambda elem: elem.get('package_count', 0), reverse=True)

    result_aux = []
    i = 1
    for item in locs:
        type = 'location'
        if is_custom(item.get('extras', {})):
            if item['name'] == c_nepal_earthquake:
                type = 'crisis'
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfLocs:
                result_aux.append(create_item(item, type, False))
                i += 1

    orgs = get_action('cached_organization_list')(context, {})
    orgs = sorted(orgs, key=lambda elem: elem.get('package_count', 0), reverse=True)

    i = 1
    type = 'organization'
    for item in orgs:
        if is_custom(item['extras']):
            result.append(create_item(item, type, False))
        else:
            if i <= NoOfOrgs:
                result_aux.append(create_item(item, type, False))
                i += 1

    result.extend(result_aux)
    return result


def is_custom(extras):
    for item in extras:
        if 'key' in item and ('custom_loc' == item['key'] or 'custom_org' == item['key']) and '1' == item['value']:
            return True
    return False


def create_item(item, type, follow=False):
    return {'id': item['id'], 'name': item['name'], 'display_name': item['display_name'], 'type': type,
            'follow': follow}


def hdx_send_reset_link(context, data_dict):
    from urlparse import urljoin
    import ckan.lib.mailer as mailer
    import ckan.lib.helpers as h
    import ckanext.hdx_users.controllers.mailer as hdx_mailer

    model = context['model']

    id = data_dict.get('id', None)
    if id:
        user = model.User.get(id)
        context['user_obj'] = user
        if user is None:
            raise NotFound

    mailer.create_reset_key(user)

    subject = mailer.render_jinja2('emails/reset_password_subject.txt', {'site_title': config.get('ckan.site_title')})
    # Make sure we only use the first line
    subject = subject.split('\n')[0]

    reset_link = user_fullname = recipient_mail = None
    if user:
        recipient_mail = user.email if user.email else None
        user_fullname = user.fullname or ''
        reset_link = urljoin(config.get('ckan.site_url'),
                             h.url_for(controller='user', action='perform_reset', id=user.id, key=user.reset_key))

    body = u"""\
                <p>Dear {fullname}, </p>
                <p>You have requested your password on {site_title} to be reset.</p>
                <p>Please click on the following link to confirm this request:</p>
                <p> <a href=\"{reset_link}\">{reset_link}</a></p>
            """.format(fullname=user_fullname, site_title=config.get('ckan.site_title'),
                       reset_link=reset_link)

    if recipient_mail:
        hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': recipient_mail}], subject, body)