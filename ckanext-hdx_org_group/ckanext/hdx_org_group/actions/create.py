import random
from socket import error as socket_error
import ckan.logic as logic
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.navl.dictization_functions as core_df
import ckan.logic.action.create as core_create
import ckan.logic.schema as core_schema
import ckan.model as core_model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.reset_password as reset_password

_validate = core_df.validate
_check_access = tk.check_access
_get_action = tk.get_action
_get_validator = tk.get_validator
_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
NotFound = tk.ObjectNotFound
config = tk.config
h = tk.h
g = tk.g
_ = tk._
NotAuthorized = tk.NotAuthorized


def hdx_user_invite(context, data_dict):
    '''Invite a new user.

    You must be authorized to create group members.

    :param email: the email of the user to be invited to the group
    :type email: string
    :param group_id: the id or name of the group
    :type group_id: string
    :param role: role of the user in the group. One of ``member``, ``editor``,
        or ``admin``
    :type role: string

    :returns: the newly created user
    :rtype: dictionary
    '''
    import string
    _check_access('user_invite', context, data_dict)

    schema = context.get('schema', core_schema.default_user_invite_schema())
    data, errors = _validate(data_dict, schema, context)
    if errors:
        raise ValidationError(errors)

    model = context['model']
    group = model.Group.get(data['group_id'])
    if not group:
        raise NotFound()

    name = core_create._get_random_username_from_email(data['email'])
    # Choose a password. However it will not be used - the invitee will not be
    # told it - they will need to reset it
    while True:
        password = ''.join(random.SystemRandom().choice(
            string.ascii_lowercase + string.ascii_uppercase + string.digits)
                           for _ in range(12))
        # Occasionally it won't meet the constraints, so check
        errors = {}
        _get_validator('user_password_validator')('password', {'password': password}, errors, None)
        if not errors:
            break

    data['name'] = name
    data['password'] = password
    data['state'] = core_model.State.PENDING
    user_dict = _get_action('user_create')(context, data)
    user = core_model.User.get(user_dict['id'])
    member_dict = {
        'username': user.id,
        'id': data['group_id'],
        'role': data['role']
    }

    if group.is_organization:
        _get_action('organization_member_create')(context, member_dict)
        group_dict = _get_action('organization_show')(context,
                                                      {'id': data['group_id']})
    else:
        _get_action('group_member_create')(context, member_dict)
        group_dict = _get_action('group_show')(context,
                                               {'id': data['group_id']})
    try:
        expiration_in_hours = int(config.get('hdx.password.invitation_reset_key.expiration_in_hours', 48))
        reset_password.create_reset_key(user, expiration_in_minutes=60 * expiration_in_hours)
        subject = u'HDX account creation'
        email_data = {
            'org_name': group_dict.get('display_name'),
            'capacity': data['role'],
            'user_fullname': g.userobj.display_name,
            'expiration_in_hours': expiration_in_hours,
            'user_reset_link': h.url_for(controller='user',
                                         action='perform_reset',
                                         id=user.id,
                                         key=user.reset_key,
                                         qualified=True)
        }
        hdx_mailer.mail_recipient([{'display_name': user.email, 'email': user.email}],
                                  subject, email_data,
                                  snippet='email/content/new_account_confirmation_to_user.html')

        subject = u'New HDX user confirmation'
        email_data = {
            'org_name': group_dict.get('display_name'),
            'capacity': data['role'],
            'user_username': user.name,
            'user_email': user.email,
        }
        admin_list = get_organization_admins(group_dict.get('id'), user.email)
        hdx_mailer.mail_recipient(admin_list,
                                  subject, email_data, footer='hdx@un.org',
                                  snippet='email/content/new_account_confirmation_to_admins.html')
    except (socket_error, Exception) as error:
        # Email could not be sent, delete the pending user
        _get_action('user_delete')(context, {'id': user.id})
        _err_str = 'Error sending the invite email, the user was not created: {0}'.format(error)
        msg = _(_err_str)
        raise ValidationError({'message': msg}, error_summary=msg)

    return model_dictize.user_dictize(user, context)


def get_organization_admins(group_id, skip_email=''):
    admin_list = []
    admins = set(core_model.Session.query(core_model.User).join(core_model.Member,
                                                                core_model.User.id == core_model.Member.table_id).
                 filter(core_model.Member.table_name == "user").filter(core_model.Member.group_id == group_id).
                 filter(core_model.Member.state == 'active').filter(core_model.Member.capacity == 'admin'))
    for admin in admins:
        if skip_email != admin.email:
            admin_list.append({'display_name': admin.display_name, 'email': admin.email})
    return admin_list


def hdx_member_create(context, data_dict=None):
    '''Make an object (e.g. a user, dataset or group) a member of a group.

    If the object is already a member of the group then the capacity of the
    membership will be updated.

    You must be authorized to edit the group.

    :param id: the id or name of the group to add the object to
    :type id: string
    :param object: the id or name of the object to add
    :type object: string
    :param object_type: the type of the object being added, e.g. ``'package'``
        or ``'user'``
    :type object_type: string
    :param capacity: the capacity of the membership
    :type capacity: string

    :returns: the newly created (or updated) membership
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']

    group_id, obj_id, obj_type, capacity = \
        _get_or_bust(data_dict, ['id', 'object', 'object_type', 'capacity'])

    group = model.Group.get(group_id)
    if not group:
        raise NotFound('Group was not found.')

    obj_class = logic.model_name_to_class(model, obj_type)
    obj = obj_class.get(obj_id)
    if not obj:
        raise NotFound('%s was not found.' % obj_type.title())

    _check_access('member_create', context, data_dict)

    # Look up existing, in case it exists. For members, we want all, not only active. It will not create other members,
    # but reuse one previous member. Result is ordered by state, which displays the 'active' members first
    # in case they exist. This avoids duplicated members
    if obj_type == 'user':
        member = model.Session.query(model.Member). \
            filter(model.Member.table_name == obj_type). \
            filter(model.Member.table_id == obj.id). \
            filter(model.Member.group_id == group.id). \
            order_by(model.Member.state).first()
    else:
        member = model.Session.query(model.Member). \
            filter(model.Member.table_name == obj_type). \
            filter(model.Member.table_id == obj.id). \
            filter(model.Member.group_id == group.id). \
            filter(model.Member.state == 'active').first()
    if member:
        user_obj = model.User.get(user)
        if member.table_name == u'user' and \
            member.table_id == user_obj.id and \
            member.capacity == u'admin' and \
            capacity != u'admin':
            raise NotAuthorized("Administrators cannot revoke their "
                                "own admin status")
    else:
        member = model.Member(table_name=obj_type,
                              table_id=obj.id,
                              group_id=group.id,
                              state='active')
        member.group = group
    member.capacity = capacity
    if obj_type == 'user':
        member.state = 'active'
    model.Session.add(member)
    model.repo.commit()

    return model_dictize.member_dictize(member, context)
