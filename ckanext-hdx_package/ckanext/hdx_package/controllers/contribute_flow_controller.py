import json
import uuid

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.lib.helpers as h

from ckan.common import _, request, response, c
from ckan.lib.search import SearchIndexError
from ckan.controllers.api import CONTENT_TYPES

tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

abort = base.abort


class ContributeFlowController(base.BaseController):

    def edit(self, id, data=None, errors=None, error_summary=None):
        return self.new(id=id, data=data, errors=errors, error_summary=error_summary, action_name='package_update')

    def new(self, id=None, data=None, errors=None, error_summary=None, action_name='package_create'):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}
        try:
            logic.check_access(action_name, context)
        except logic.NotAuthorized:
            abort(401, _('Unauthorized to create a package'))

        save_type = request.POST.get('save')
        dataset_dict = None
        errors = None
        error_summary = None

        status_code = 200
        abort_message = None
        try:
            if request.POST and save_type:
                # update or create dataset
                dataset_dict, errors, error_summary = self._save_or_update(context)

            else:
                if id:
                    # show dataset in case of edit
                    dataset_dict = logic.get_action('package_show')(context, {'id': id})

        except logic.NotAuthorized, e:
            status_code = 401
            ex_msg = e.message if hasattr(e, 'message') else str(e)
            abort_message = _('Unauthorized action: ') + ex_msg
        except logic.NotFound, e:
            status_code = 404
            abort_message = _('Dataset not found')

        except NoOrganization, e:
            status_code = 400
            ex_msg = e.message if hasattr(e, 'message') else str(e)
            abort_message = _('User has no organization:') + ex_msg
        except dict_fns.DataError, e:
            status_code = 400
            ex_msg = e.message if hasattr(e, 'message') else str(e)
            abort_message = _(u'Integrity Error:') + ex_msg
        except SearchIndexError, e:
            try:
                exc_str = unicode(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = unicode(str(e))
            status_code = 500
            abort_message = _(u'Unable to add package to search index.') + exc_str

        if status_code != 200:
            return self._abort(save_type, status_code, abort_message)

        return self._prepare_and_render(save_type=save_type, data=dataset_dict, errors=errors,
                                        error_summary=error_summary)

    def _abort(self, save_type, status_code, message):
        if '-json' in save_type:
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            response_data = {
                'aborted': True,
                'message': message,
                'status_code': status_code
            }
            return json.dumps(response_data)
        else:
            abort(status_code, message)

    def _prepare_and_render(self, save_type='', data=None, errors=None, error_summary=None):

        save_type = save_type if save_type else ''
        template_data = {
            'data': data,
            'errors': errors,
            'error_summary': error_summary,
            'aborted': False
        }

        if '-json' in save_type:
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(template_data)
        else:
            return base.render('contribute_flow/create_edit.html', extra_vars=template_data)

    def _save_or_update(self, context, package_type=None):
        data_dict = {}
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.POST))))

            data_dict['type'] = package_type
            del data_dict['save']

            context['message'] = data_dict.get('log_message', '')

            dataset_id = data_dict.get('id')

            pkg_dict = {}
            if dataset_id:
                pkg_dict = logic.get_action('package_update')(context, data_dict)
            else:
                self._autofill_mandatory_fields(data_dict)
                pkg_dict = logic.get_action('package_create')(context, data_dict)

            return (pkg_dict, {}, {})

        except logic.ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary

            return data_dict, errors, error_summary

    def _autofill_mandatory_fields(self, data_dict):
        '''
        Adds to the data_dict the missing mandatory fields

        :param data_dict: dictionary with request parameters
        :type data_dict: dict
        '''

        if 'private' not in data_dict:
            data_dict['private'] = 'True'

        if 'name' not in data_dict:
            random_string = str(uuid.uuid4()).replace('-', '')
            user = c.user or c.author
            name = '{}_{}'.format(user, random_string)
            data_dict['name'] = name

        if 'license_id' not in data_dict:
            data_dict['license_id'] = 'cc-by'

        if 'notes' not in data_dict:
            data_dict['notes'] = ''

        org_id = data_dict.get('owner_org')
        selected_org = None
        if not org_id:
            orgs = h.organizations_available('create_dataset')
            if len(orgs) == 0:
                raise NoOrganization(_('The user needs to belong to at least 1 organisation'))
            else:
                selected_org = orgs[1]
                org_id = selected_org.get('id')
                data_dict['owner_org'] = org_id

        source = data_dict.get('dataset_source')
        if not source:
            if selected_org:
                source = selected_org.get('title')
            else:
                context = {'user': c.user}
                selected_org = logic.get_action('organization_show')(context, {'id': org_id, 'include_datasets': False})
                source = selected_org.get('title')
            data_dict['dataset_source'] = source


class NoOrganization(logic.ActionError):
    pass
