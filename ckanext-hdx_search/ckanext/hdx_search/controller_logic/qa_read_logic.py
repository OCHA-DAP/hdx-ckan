import ckan.plugins.toolkit as tk

import ckanext.hdx_package.helpers.membership_data as membership

g = tk.g


class QAReadLogic(object):

    def __init__(self):
        super(QAReadLogic, self).__init__()
        self.membership = None

    def read(self):
        self.membership = membership.get_membership_by_user(g.user, None, g.userobj)
        return self
