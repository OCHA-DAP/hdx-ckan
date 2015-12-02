import ckan.lib.base as base

class ContributeFlowController(base.BaseController):

    def new(self):
        return base.render('contribute_flow/create_edit.html')