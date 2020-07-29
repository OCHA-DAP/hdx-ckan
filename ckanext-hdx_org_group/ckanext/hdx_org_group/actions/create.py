import random
import ckan.lib.navl.dictization_functions as core_df
import ckan.logic as logic
import ckan.logic.action.create as core_create
import ckan.logic.schema as core_schema
import ckan.model as core_model
import ckan.lib.dictization.model_dictize as model_dictize
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckan.lib.mailer as core_mailer
import ckan.lib.helpers as h

from socket import error as socket_error

from ckan.common import _



_validate = core_df.validate
_check_access = logic.check_access
_get_action = logic.get_action
ValidationError = logic.ValidationError
NotFound = logic.NotFound
_get_or_bust = logic.get_or_bust

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
        logic.validators.user_password_validator(
            'password', {'password': password}, errors, None)
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
        core_mailer.create_reset_key(user)
        subject = u'HDX account creation'
        email_data = {
            'org_name': group_dict.get('display_name'),
            'capacity': data['role'],
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
                                  subject, email_data,
                                  snippet='email/content/new_account_confirmation_to_admins.html')
    except (socket_error, Exception) as error:
        # Email could not be sent, delete the pending user
        _get_action('user_delete')(context, {'id': user.id})
        _err_str = 'Error sending the invite email, the user was not created: {0}'.format(error)
        msg = _(_err_str)
        raise ValidationError({'message': msg}, error_summary=msg)

    return model_dictize.user_dictize(user, context)


def get_organization_admins(group_id, skip_email):
    admin_list = []
    admins = set(core_model.Session.query(core_model.User).join(core_model.Member,
                                                                core_model.User.id == core_model.Member.table_id).
                 filter(core_model.Member.table_name == "user").filter(core_model.Member.group_id == group_id).
                 filter(core_model.Member.state == 'active').filter(core_model.Member.capacity == 'admin'))
    for admin in admins:
        if skip_email != admin.email:
            admin_list.append({'display_name': admin.display_name, 'email': admin.email})
    return admin_list
