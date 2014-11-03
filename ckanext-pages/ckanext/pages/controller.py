import ckan.plugins as p

_ = p.toolkit._

class PagesController(p.toolkit.BaseController):
    controller = 'ckanext.pages.controller:PagesController'

    def _get_group_dict(self, id):
        ''' returns the result of group_show action or aborts if there is a
        problem '''

    def _template_setup_org(self, id):
        if not id:
            return
        # we need the org for the rest of the page
        context = {'for_view': True}
        try:
            p.toolkit.c.group_dict = p.toolkit.get_action('organization_show')(context, {'id': id})
        except p.toolkit.ObjectNotFound:
            p.toolkit.abort(404, _('Organization not found'))
        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401, _('Unauthorized to read organization %s') % id)

    def org_show(self, id, page=None):
        if page:
            page = page[1:]
        self._template_setup_org(id)
        if page is '':
            return self._org_list_pages(id)
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': p.toolkit.c.group_dict['id'],
                       'page': page,}
        )
        if _page is None:
            return self._org_list_pages(id)
        p.toolkit.c.page = _page
        return p.toolkit.render('ckanext_pages/organization_page.html')

    def _org_list_pages(self, id):
        p.toolkit.c.pages_dict = p.toolkit.get_action('ckanext_pages_list')(
            data_dict={'org_id': p.toolkit.c.group_dict['id']}
        )
        return p.toolkit.render('ckanext_pages/organization_page_list.html')


    def org_delete(self, id, page):
        self._template_setup_org(id)
        page = page[1:]
        if 'cancel' in p.toolkit.request.params:
            p.toolkit.redirect_to(controller=self.controller, action='org_edit', id=p.toolkit.c.group_dict['name'], page='/' + page)

  ##      try:
  ##          self._check_access('group_delete', {}, {'id': id})
  ##      except p.toolkit.NotAuthorized:
  ##          p.toolkit.abort(401, _('Unauthorized to delete page'))

        try:
            if p.toolkit.request.method == 'POST':
                p.toolkit.get_action('ckanext_pages_delete')({}, {'org_id': p.toolkit.c.group_dict['id'], 'page': page})
                p.toolkit.redirect_to(controller=self.controller, action='org_show', id=id, page='')
            else:
                p.toolkit.abort(404, _('Page Not Found'))
        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401, _('Unauthorized to delete page'))
        except p.toolkit.ObjectNotFound:
            p.toolkit.abort(404, _('Group not found'))
        return p.toolkit.render('ckanext_pages/confirm_delete.html', {'page': page})


    def org_edit(self, id, page=None, data=None, errors=None, error_summary=None):
        self._template_setup_org(id)
        if page:
            page = page[1:]
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': p.toolkit.c.group_dict['id'],
                       'page': page,}
        )
        if _page is None:
            _page = {}

        if p.toolkit.request.method == 'POST' and not data:
            data = p.toolkit.request.POST
            items = ['title', 'name', 'content', 'private']
            # update config from form
            for item in items:
                if item in data:
                    _page[item] = data[item]
            _page['org_id'] = p.toolkit.c.group_dict['id'],
            _page['page'] = page
            try:
                junk = p.toolkit.get_action('ckanext_pages_update')(
                    data_dict=_page
                )
            except p.toolkit.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.org_edit(id, '/' + page, data,
                                 errors, error_summary)
            p.toolkit.redirect_to(p.toolkit.url_for('organization_pages', id=id, page='/' + _page['name']))

        if not data:
            data = _page

        errors = errors or {}
        error_summary = error_summary or {}

        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'page': page}

        return p.toolkit.render('ckanext_pages/organization_page_edit.html',
                               extra_vars=vars)

    def _template_setup_group(self, id):
        if not id:
            return
        # we need the org for the rest of the page
        context = {'for_view': True}
        try:
            p.toolkit.c.group_dict = p.toolkit.get_action('group_show')(context, {'id': id})
        except p.toolkit.ObjectNotFound:
            p.toolkit.abort(404, _('Group not found'))
        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401, _('Unauthorized to read group %s') % id)


    def group_show(self, id, page=None):
        if page:
            page = page[1:]
        self._template_setup_group(id)
        if page is '':
            return self._group_list_pages(id)
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': p.toolkit.c.group_dict['id'],
                       'page': page,}
        )
        if _page is None:
            return self._group_list_pages(id)
        p.toolkit.c.page = _page
        return p.toolkit.render('ckanext_pages/group_page.html')

    def _group_list_pages(self, id):
        p.toolkit.c.pages_dict = p.toolkit.get_action('ckanext_pages_list')(
            data_dict={'org_id': p.toolkit.c.group_dict['id']}
        )
        return p.toolkit.render('ckanext_pages/group_page_list.html')

    def group_edit(self, id, page=None, data=None, errors=None, error_summary=None):
        self._template_setup_group(id)
        if page:
            page = page[1:]
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': p.toolkit.c.group_dict['id'],
                       'page': page,}
        )
        if _page is None:
            _page = {}

        if p.toolkit.request.method == 'POST' and not data:
            data = p.toolkit.request.POST
            items = ['title', 'name', 'content', 'private']
            # update config from form
            for item in items:
                if item in data:
                    _page[item] = data[item]
            _page['org_id'] = p.toolkit.c.group_dict['id']
            _page['page'] = page
            try:
                junk = p.toolkit.get_action('ckanext_pages_update')(
                    data_dict=_page
                )
            except p.toolkit.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.group_edit(id, '/' + page, data,
                                 errors, error_summary)
            p.toolkit.redirect_to(p.toolkit.url_for('group_pages', id=id, page='/' + _page['name']))

        if not data:
            data = _page

        errors = errors or {}
        error_summary = error_summary or {}

        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'page': page}

        return p.toolkit.render('ckanext_pages/group_page_edit.html',
                               extra_vars=vars)


    def pages_show(self, page=None):
        if page:
            page = page[1:]
        if not page:
            return self._pages_list_pages()
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': None,
                       'page': page,}
        )
        if _page is None:
            return self._pages_list_pages()
        p.toolkit.c.page = _page
        return p.toolkit.render('ckanext_pages/page.html')

    def _pages_list_pages(self):
        p.toolkit.c.pages_dict = p.toolkit.get_action('ckanext_pages_list')(
            data_dict={'org_id': None}
        )
        return p.toolkit.render('ckanext_pages/pages_list.html')

    def pages_delete(self, page):
        page = page[1:]
        if 'cancel' in p.toolkit.request.params:
            p.toolkit.redirect_to(controller=self.controller, action='pages_edit', page='/' + page)


        try:
            if p.toolkit.request.method == 'POST':
                p.toolkit.get_action('ckanext_pages_delete')({}, {'page': page})
                p.toolkit.redirect_to(controller=self.controller, action='pages_show', page='')
            else:
                p.toolkit.abort(404, _('Page Not Found'))
        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401, _('Unauthorized to delete page'))
        except p.toolkit.ObjectNotFound:
            p.toolkit.abort(404, _('Group not found'))
        return p.toolkit.render('ckanext_pages/confirm_delete.html', {'page': page})


    def pages_edit(self, page=None, data=None, errors=None, error_summary=None):
        if page:
            page = page[1:]
        _page = p.toolkit.get_action('ckanext_pages_show')(
            data_dict={'org_id': None,
                       'page': page,}
        )
        if _page is None:
            _page = {}

        if p.toolkit.request.method == 'POST' and not data:
            data = p.toolkit.request.POST
            items = ['title', 'name', 'content', 'private', 'order']

            # update config from form
            for item in items:
                if item in data:
                    _page[item] = data[item]
            _page['org_id'] = None
            _page['page'] = page
            try:
                junk = p.toolkit.get_action('ckanext_pages_update')(
                    data_dict=_page
                )
            except p.toolkit.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
                return self.pages_edit('/' + page, data,
                                 errors, error_summary)
            p.toolkit.redirect_to(p.toolkit.url_for('pages_show', page='/' + _page['name']))

        try:
            p.toolkit.check_access('ckanext_pages_update', {'user': p.toolkit.c.user or p.toolkit.c.author})
        except p.toolkit.NotAuthorized:
            p.toolkit.abort(401, _('Unauthorized to create or edit a page'))

        if not data:
            data = _page

        errors = errors or {}
        error_summary = error_summary or {}

        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'page': page}

        return p.toolkit.render('ckanext_pages/pages_edit.html',
                               extra_vars=vars)



