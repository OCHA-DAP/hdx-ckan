from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender


class FirstLoginAnalyticsSender(AbstractAnalyticsSender):

    @classmethod
    def _get_action_name(cls) -> str:
        return 'first login'

    @classmethod
    def _replace_special_chars_with_space(cls, input_str: str) -> str:
        if input_str:
            return input_str.replace('_', ' ').replace('-', ' ')

    def __init__(self, onboarding_start: str, account_choice: str):
        super().__init__()
        cleaned_onboarding_start = self._replace_special_chars_with_space(onboarding_start)
        cleaned_account_choice = self._replace_special_chars_with_space(account_choice)

        self.analytics_dict = {
            'event_name': self._get_action_name(),
            'mixpanel_meta': {
                'onboarding start': cleaned_onboarding_start,
                'account choice': cleaned_account_choice
            },
            'ga_meta': {
                'ec': 'organization',  # event category
                'ea': self._get_action_name(),  # event action
                'el': cleaned_account_choice,  # event label
                'cd1': cleaned_onboarding_start
            }
        }

