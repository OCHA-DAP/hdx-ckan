from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender


class RemoveMemberAnalyticsSender(AbstractAnalyticsSender):

    @classmethod
    def _get_action_name(cls):
        return 'member remove'

    def __init__(self, org_id, org_name):
        super(RemoveMemberAnalyticsSender, self).__init__()
        self.analytics_dict = {
            'event_name': self._get_action_name(),
            'mixpanel_meta': {
                'org name': org_name,
                'org id': org_id
            },
            'ga_meta': {
                'ec': 'organization',  # event category
                'ea': self._get_action_name(),  # event action
                'el': org_name,  # event label
                'cd1': org_name
            }
        }



class ChangeMemberAnalyticsSender(RemoveMemberAnalyticsSender):

    @classmethod
    def _get_action_name(cls):
        return 'member change'


class AddMemberAnalyticsSender(RemoveMemberAnalyticsSender):

    @classmethod
    def _get_action_name(cls):
        return 'member add'

    def __init__(self, org_id, org_name):
        super(AddMemberAnalyticsSender, self).__init__(org_id, org_name)
        self.analytics_dict['mixpanel_meta']['add method'] = 'by invitation'
