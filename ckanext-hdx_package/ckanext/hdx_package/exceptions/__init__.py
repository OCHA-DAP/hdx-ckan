import ckan.logic as logic

class NoOrganization(logic.ActionError):
    pass


class WrongResourceParamName(logic.ActionError):
    pass