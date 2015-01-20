import urllib

import ckan.model as model
import ckan.logic as logic
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as df
import ckan.lib.dictization as dictization

from ckan.common import _, c


abort = base.abort
_get_action = logic.get_action


class RelatedController(base.BaseController):

    def edit(self, id, related_id):
        return self._hdx_edit(id, related_id, True)

    def _hdx_edit(self, id, related_id, is_edit):
        #Taken from ckan/controller/related.py, paired down to just edits
        """
        Edit and New were too similar and so I've put the code together
        and try and do as much up front as possible.
        """
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'for_view': True}
        data_dict = {}

        tpl = 'related/edit.html'
        auth_name = 'related_update'
        auth_dict = {'id': related_id}
        action_name = 'related_update'

        try:
            related = logic.get_action('related_show')(
                    context, {'id': related_id})
        except logic.NotFound:
            base.abort(404, _('Related item not found'))
        
        try:
            logic.check_access(auth_name, context, auth_dict)
        except logic.NotAuthorized:
            #If user can edit package, user can edit related item
            try:
                logic.check_access('package_update', {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}, {'id': id})
            except logic.NotAuthorized:
                base.abort(401, base._('Not authorized'))
            
        try:
            c.pkg_dict = logic.get_action('package_show')(context, {'id': id})
        except logic.NotFound:
            base.abort(404, _('Package not found'))

        data, errors, error_summary = {}, {}, {}

        if base.request.method == "POST":
            try:
                data = logic.clean_dict(
                    df.unflatten(
                        logic.tuplize_dict(
                            logic.parse_params(base.request.params))))

                data['id'] = related_id
                related = self.related_update(context, data)
                h.flash_success(_("Related item was successfully updated"))

                h.redirect_to(
                    controller='ckanext.hdx_package.controllers.dataset_controller:DatasetController', action='read', id=c.pkg_dict['name'])
            except df.DataError:
                base.abort(400, _(u'Integrity Error'))
            except logic.ValidationError, e:
                errors = e.error_dict
                error_summary = e.error_summary
        else:
            data = related

        c.types = self._type_options()

        c.pkg_id = id
        vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        c.form = base.render("related/edit_form.html", extra_vars=vars)
        return base.render(tpl)

    def related_update(self, context, data_dict):
        '''Update a related item.

        You must be the owner of a related item to update it.

        For further parameters see ``related_create()``.

        :param id: the id of the related item to update
        :type id: string

        :returns: the updated related item
        :rtype: dictionary

        '''
        model = context['model']
        id = logic.get_or_bust(data_dict, "id")

        session = context['session']
        schema = context.get('schema') or logic.schema.default_update_related_schema()

        related = model.Related.get(id)
        context["related"] = related

        if not related:
            logging.error('Could not find related ' + id)
            raise NotFound(_('Item was not found.'))

        data, errors = df.validate(data_dict, schema, context)
        if errors:
            model.Session.rollback()
            raise ValidationError(errors)

        related = dictization.model_save.related_dict_save(data, context)

        dataset_dict = None
        if 'package' in context:
            dataset = context['package']
            dataset_dict = dictization.table_dictize(dataset, context)

        related_dict = dictization.model_dictize.related_dictize(related, context)
        activity_dict = {
            'user_id': context['user'],
            'object_id': related.id,
            'activity_type': 'changed related item',
        }
        activity_dict['data'] = {
            'related': related_dict,
            'dataset': dataset_dict,
        }
        activity_create_context = {
            'model': model,
            'user': context['user'],
            'defer_commit': True,
            'ignore_auth': True,
            'session': session
        }

        logic.get_action('activity_create')(activity_create_context, activity_dict)

        if not context.get('defer_commit'):
            model.repo.commit()
        return dictization.model_dictize.related_dictize(related, context)

    def _type_options(self):
        '''
        A tuple of options for the different related types for use in
        the form.select() template macro.
        '''
        return ({"text": _("API"), "value": "api"},
                {"text": _("Application"), "value": "application"},
                {"text": _("Idea"), "value": "idea"},
                {"text": _("News Article"), "value": "news_article"},
                {"text": _("Paper"), "value": "paper"},
                {"text": _("Post"), "value": "post"},
                {"text": _("Visualization"), "value": "visualization"})