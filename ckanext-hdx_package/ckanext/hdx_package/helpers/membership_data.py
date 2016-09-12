import logging
import collections

import ckan.model as model
import ckan.logic as logic

log = logging.getLogger(__name__)

contributor_topics = {
    'sent a general question': 'General question',
    'asked about metadata': 'Metadata',
    'reported a problem': 'Report a problem',
    'suggested edits': 'Suggest edits',
}

group_topics = {
    'all': 'All (members, editors, admins)',
    'editors': 'All editors',
    'admins': 'All admins',
    'members': 'All members',
}

membership_data = {
    'contributor_topics': contributor_topics,
    'group_topics': group_topics
}


def get_message_groups(current_user, org_id):
    group_message_topics = {}
    context = {
        'model': model,
        'session': model.Session,
        'user': current_user,
    }
    try:
        cnt_members_list = logic.get_action('hdx_member_list')(context, {'org_id': org_id})
        if cnt_members_list.get('is_member', False):
            group_topics = [
                (
                    'all', membership_data['group_topics']['all'] + ' [' + str(
                        cnt_members_list.get('total_counter', 0)) + ']'),
                ('admins', membership_data['group_topics']['admins'] + ' [' + str(
                    cnt_members_list.get('admins_counter', 0)) + ']'),
                ('editors', membership_data['group_topics']['editors'] + ' [' + str(
                    cnt_members_list.get('editors_counter', 0)) + ']'),
                ('members', membership_data['group_topics']['members'] + ' [' + str(
                    cnt_members_list.get('members_counter', 0)) + ']')
            ]

            group_message_topics = collections.OrderedDict(group_topics)
    except Exception, e:
        log.warning("Exception occured while getting message groups for org {}".format(org_id) + str(e.args))

    return group_message_topics
