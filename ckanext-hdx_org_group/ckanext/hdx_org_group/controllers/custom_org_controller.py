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

        top_line_num_dataset = 'wfp-topline-figures'
        top_line_num_resource = 'wfp-topline-figures.csv'

        template_data = self.generate_template_data(id, top_line_num_dataset, top_line_num_resource)

        less_code = '''
        @extraLightGrayColor: red;
        @wfpBlueColor: green;
        '''

        css_dest_dir = '/organization/' + id
        compiler = less.LessCompiler(less_code, css_dest_dir, id, '123')
        compilation_result = compiler.compile_less()

        template_data['style'] = {
            'css_path': less.generate_custom_css_path(css_dest_dir, id, '123', True)
        }


        result = render(
            'organization/custom/custom_org.html', extra_vars=template_data)

        return result