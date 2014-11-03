'''
Created on Nov 3, 2014

@author: alexandru-m-g
'''


from ckan.lib import base

render = base.render

class CrisisController(base.BaseController):
    def show(self):
        return render('crisis/crisis.html')