from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender

class AddMemberAnalyticsSender(AbstractAnalyticsSender):
    def __init__(self, org_id, org_name):
        super(AddMemberAnalyticsSender, self).__init__()
        self.analytics_dict = {
            'event_name': 'member add',
            'mixpanel_meta': {
                'add method': 'by invitation',
                'org name': org_name,
                'org id': org_id
            },
            'ga_meta': {
                'ec': 'organization',  # event category
                'ea': 'member add',  # event action
                'el': org_name,  # event label
                'cd1': org_name
            }
        }