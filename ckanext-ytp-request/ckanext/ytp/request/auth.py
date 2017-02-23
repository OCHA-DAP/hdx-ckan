from ckan import new_authz, model
from ckan.common import _, c
from ckanext.ytp.request.tools import get_user_member


def _only_registered_user():
    if not new_authz.auth_is_registered_user():
        return {'success': False, 'msg': _('User is not logged in')}
    return {'success': True}


def member_request_create(context, data_dict):
    """ Create request access check """

    if not new_authz.auth_is_registered_user():
        return {'success': False, 'msg': _('User is not logged in')}

    organization_id = None if not data_dict else data_dict.get('organization_id', None)

    if organization_id:
        member = get_user_member(organization_id)
        if member:
            return {'success': False, 'msg': _('The user has already a pending request or an active membership')}

    return {'success': True}


def member_request_show(context, data_dict):
    """ Show request access check """
    return _only_registered_user()


def member_request_list(context, data_dict):
    """ List request access check """
    return _only_registered_user()


def member_request_membership_cancel(context, data_dict):
    if not c.userobj:
        return {'success': False}

    organization_id = data_dict.get("organization_id")
    member = get_user_member(organization_id, 'active')

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'active':
        return {'success': True}
    return {'success': False}


def member_request_cancel(context, data_dict):
    """ Cancel request access check.
        data_dict expects member or organization_id. See `logic.member_request_cancel`.
    """

    if not c.userobj:
        return {'success': False}
    member_id = data_dict.get("member", None)
    member = None
    if not member_id:
        organization_id = data_dict.get("organization_id")
        member = get_user_member(organization_id, 'pending')
    else:
        member = model.Member.get(member_id)

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'pending':
        return {'success': True}
    return {'success': False}


def member_request_process(context, data_dict):
    """ Approve or reject access check """

    if new_authz.is_sysadmin(context['user']):
        return {'success': True}

    user = model.User.get(context['user'])
    if not user:
        return {'success': False}

    member = model.Member.get(data_dict.get("member"))
    if not member:
        return {'success': False}

    if member.table_name != 'user':
        return {'success': False}

    query = model.Session.query(model.Member).filter(model.Member.state == 'active').filter(model.Member.table_name == 'user') \
        .filter(model.Member.capacity == 'admin').filter(model.Member.table_id == user.id).filter(model.Member.group_id == member.group_id)

    return {'success': query.count() > 0}
