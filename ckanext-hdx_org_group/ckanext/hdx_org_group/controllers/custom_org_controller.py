'''
Created on Feb 18, 2015

@author: alexandru-m-g
'''



import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.common as common

import ckanext.hdx_org_group.controllers.wfp_controller as wfp_controller
import ckanext.hdx_theme.helpers.less as less

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._


log = logging.getLogger(__name__)



class CustomOrgController(wfp_controller.WfpController):

    def org_read(self, id):

        org_info = self.get_org(id)

        template_data = self.generate_template_data(org_info)

        css_dest_dir = '/organization/' + org_info['name']

        template_data['style'] = {
            'css_path': less.generate_custom_css_path(css_dest_dir, id, org_info['modified_at'], True)
        }


        result = render(
            'organization/custom/custom_org.html', extra_vars=template_data)

        return result