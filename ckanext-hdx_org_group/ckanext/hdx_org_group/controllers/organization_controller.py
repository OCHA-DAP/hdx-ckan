'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''

import ckan.controllers.organization as org
import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base

from ckan.common import c, request, _
import ckan.lib.helpers as h

import ckanext.hdx_org_group.helpers.organization_helper as helper

abort = base.abort
render = base.render

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params


class HDXOrganizationController(org.OrganizationController):

    def index(self):
        group_type = self._guess_group_type()

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        data_dict = {'all_fields': True, 'q': q}
        sort_by = c.sort_by_selected = request.params.get('sort')
        if sort_by:
            data_dict['sort'] = sort_by
        else:
            data_dict['sort'] = 'title asc'
        try:
            self._check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        results = self._action('organization_list')(context, data_dict)

        results = helper.sort_results_case_insensitive(results, sort_by)

        def pager_url(q=None, page=None):
            if sort_by:
                url = h.url_for(
                    'organizations_index', page=page, sort=sort_by)
            else:
                url = h.url_for('organizations_index', page=page)
            return url


        c.page = h.Page(
            collection=results,
            page=request.params.get('page', 1),
            url=pager_url,
            items_per_page=21
        )
        return render(self._index_template(group_type))

