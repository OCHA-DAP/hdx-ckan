'''
Created on Apr 30, 2014

@author: alexandru-m-g
'''

import ckan.controllers.user as user
import ckan.lib.helpers as h
import ckan.lib.base as base

from ckan.common import c

render = base.render

class LoginController (user.UserController):
    def contribute(self, error=None):
        self.login(error)
        vars    = {'contribute':True}
        return render('user/login.html', extra_vars=vars)
         
