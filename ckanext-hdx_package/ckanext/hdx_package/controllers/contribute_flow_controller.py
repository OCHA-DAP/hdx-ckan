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

    def new(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}
        try:
            logic.check_access('package_create', context)
        except logic.NotAuthorized:
            abort(401, _('Unauthorized to create a package'))

        save_type = request.POST.get('save')

        if request.POST and save_type:
            dataset_dict, errors, error_summary = self._save_new(context)

            template_data = {
                'data': dataset_dict,
                'errors': errors,
                'error_summary': error_summary,
            }

            if '-json' in save_type:
                response.headers['Content-Type'] = CONTENT_TYPES['json']
                return json.dumps(template_data)
            else:
                return base.render('contribute_flow/create_edit.html', extra_vars=template_data)
        else:
            return base.render('contribute_flow/create_edit.html')

    def _save_new(self, context, package_type=None):

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

        except logic.NotAuthorized:
            abort(401, _('Unauthorized to read package %s') % '')
        except logic.NotFound, e:
            abort(404, _('Dataset not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except SearchIndexError, e:
            try:
                exc_str = unicode(repr(e.args))
            except Exception:  # We don't like bare excepts
                exc_str = unicode(str(e))
            abort(500, _(u'Unable to add package to search index.') + exc_str)
        except logic.ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary

            return (data_dict, errors, error_summary)

    def _autofill_mandatory_fields(self, data_dict):
        '''
        Adds to the data_dict the missing mandatory fields

        :param data_dict: dictionary with request parameters
        :type data_dict: dict
        '''

        if 'private' not in data_dict:
            data_dict['private'] = 'False'

        if 'name' not in data_dict:
            random_string = str(uuid.uuid4()).replace('-', '')
            user = c.user or c.author
            name = '{}_{}'.format(user, random_string)
            data_dict['name'] = name

        if 'license' not in data_dict:
            data_dict['license'] = 'cc-by'

        if 'notes' not in data_dict:
            data_dict['notes'] = ''

        org_id = data_dict.get('owner_org')
        source = data_dict.get('dataset_source')
        if not org_id or not source:
            orgs = h.organizations_available('create_dataset')
            if len(orgs) == 0:
                abort(404, _('The user needs to belong to at least 1 organisation'))
            else:
                org = orgs[1]
                data_dict['owner_org'] = org_id if org_id else org.get('id')
                data_dict['dataset_source'] = source if source else org.get('title')

    def _find_user_organization(self):
        pass
