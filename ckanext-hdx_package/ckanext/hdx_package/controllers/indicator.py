import ckan.controllers.package as package
import ckan.lib.base as base

render = base.render

class IndicatorController(package.PackageController):

    def read(self, id, format='html'):
        super(IndicatorController, self).read(id, format)
        return render('indicator/read.html')

