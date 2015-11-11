import ckan.lib.base as base


class PagesController(base.BaseController):

    def new(self):
        return base.render('pages/edit_page.html')

    def edit(self, id):
        return None