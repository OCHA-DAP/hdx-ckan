import logging
# import datetime
#
# from pylons import config
# import sqlalchemy

# import ckan.lib.dictization
import ckan.plugins.toolkit as tk
import ckan.lib.dictization.model_dictize as model_dictize
# import ckan.model.misc as misc
# import ckan.plugins as plugins
# import ckan.lib.plugins as lib_plugins
import ckan.new_authz as new_authz
# import beaker.cache as bcache
# import ckan.model as model
#
# import ckanext.hdx_package.helpers.caching as caching
# import ckanext.hdx_theme.helpers.counting_actions as counting
# import ckanext.hdx_theme.util.mail as hdx_mail
#
# from ckan.common import c, _

import ckan.logic as logic

log = logging.getLogger(__name__)
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
NotFound = logic.NotFound


def hdx_user_show(context, data_dict):
    '''Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary
    :param include_datasets: Include a list of datasets the user has created.
        If it is the same user or a sysadmin requesting, it includes datasets
        that are draft or private.
        (optional, default:``False``, limit:50)
    :type include_datasets: boolean
    :param include_num_followers: Include the number of followers the user has
         (optional, default:``False``)
    :type include_num_followers: boolean

    :returns: the details of the user. Includes email_hash, number_of_edits and
        number_created_packages (which excludes draft or private datasets
        unless it is the same user or sysadmin making the request). Excludes
        the password (hash) and reset_key. If it is the same user or a
        sysadmin requesting, the email and apikey are included.
    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id', None)
    provided_user = data_dict.get('user_obj', None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
        if user_obj is None:
            raise NotFound
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise NotFound

    _check_access('user_show', context, data_dict)

    user_dict = model_dictize.user_dictize(user_obj, context)

    # include private and draft datasets?
    requester = context.get('user')
    if requester:
        requester_looking_at_own_account = requester == user_obj.name
        include_private_and_draft_datasets = \
            new_authz.is_sysadmin(requester) or \
            requester_looking_at_own_account
    else:
        include_private_and_draft_datasets = False
    context['count_private_and_draft_datasets'] = \
        include_private_and_draft_datasets

    user_dict = model_dictize.user_dictize(user_obj, context)

    if context.get('return_minimal'):
        log.warning('Use of the "return_minimal" in user_show is '
                    'deprecated.')
        return user_dict

    if data_dict.get('include_datasets', False):
        offset = data_dict.get('offset', 0)
        limit = data_dict.get('limit', 20)
        user_dict['datasets'] = []

        dataset_q = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj, role=model.Role.ADMIN).offset(offset).limit(limit)

        if not include_private_and_draft_datasets:
            dataset_q = dataset_q \
                .filter_by(state='active') \
                .filter_by(private=False)
        else:
            dataset_q = dataset_q \
                .filter(model.Package.state != 'deleted')

        dataset_q_counter = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj, role=model.Role.ADMIN).count()

        for dataset in dataset_q:
            try:
                dataset_dict = logic.get_action('package_show')(
                    context, {'id': dataset.id})
                del context['package']
            except logic.NotAuthorized:
                continue
            user_dict['datasets'].append(dataset_dict)

    revisions_q = model.Session.query(model.Revision
                                      ).filter_by(author=user_obj.name)

    revisions_list = []
    for revision in revisions_q.limit(20).all():
        revision_dict = tk.get_action('revision_show')(context, {'id': revision.id})
        revision_dict['state'] = revision.state
        revisions_list.append(revision_dict)
    user_dict['activity'] = revisions_list

    user_dict['num_followers'] = tk.get_action('user_follower_count')(
        {'model': model, 'session': model.Session},
        {'id': user_dict['id']})
    user_dict['total_count'] = dataset_q_counter
    return user_dict
