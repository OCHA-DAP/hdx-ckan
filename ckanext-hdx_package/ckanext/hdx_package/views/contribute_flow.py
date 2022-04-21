import json
import logging

from flask import Blueprint, make_response
from six import text_type

import ckan.lib.navl.dictization_functions as dict_fns
import ckan.model as model
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckanext.hdx_package.helpers.analytics as analytics

from ckan.views.api import CONTENT_TYPES
from ckan.lib.search import SearchIndexError
from ckanext.hdx_package.controller_logic.contribute_flow_read_logic import ContributeFlowReadLogic
from ckanext.hdx_package.controller_logic.contribute_flow_write_logic import ContributeFlowWriteLogic
from ckanext.hdx_package.exceptions import NoOrganization

log = logging.getLogger(__name__)

g = tk.g
h = tk.h
_ = tk._
_get_action = tk.get_action
_check_access = tk.check_access
request = tk.request
abort = tk.abort
render = tk.render
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

hdx_contribute = Blueprint(u'hdx_contribute', __name__, url_prefix=u'/contribute')


def edit(id):
    return new(id=id, action_name='package_update')


def new(id=None, action_name='package_create'):
    context = {
        'model': model, 'session': model.Session,
        'user': g.user or g.author, 'auth_user_obj': g.userobj,
        'save': 'save' in request.form,
        'contribute_flow': True
    }
    dataset_dict = None
    try:
        if id:
            dataset_dict = _get_action('package_show_edit')(context, {'id': id})
            owner_org = dataset_dict.get('organization')
            if owner_org:
                dataset_dict['owner_org_name'] = owner_org.get('name')
        _check_access(action_name, context, dataset_dict)
    except NotAuthorized as e:
        if g.userobj or g.user:
            return h.redirect_to('dashboard.organizations')
        return abort(403, _('Unauthorized to create a package'))

    save_type = request.form.get('save')

    errors = None
    error_summary = None

    status_code = 200
    abort_message = None

    try:
        if request.method == 'POST' and request.form and save_type:
            # update or create dataset
            dataset_dict, errors, error_summary = _save_or_update(context)
        else:
            if id:
                # show dataset in case of edit
                read_logic = ContributeFlowReadLogic(dataset_dict)
                read_logic.process_all()

    except NotAuthorized as e:
        status_code = 401
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        abort_message = _('Unauthorized action: ') + ex_msg
    except NotFound as e:
        log.info("Maintainer or user not found!")
        abort_message = _('Dataset/user not found')
    except NoOrganization as e:
        status_code = 400
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        abort_message = _('User has no organization:') + ex_msg
    except dict_fns.DataError as e:
        status_code = 400
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        abort_message = _(u'Integrity Error:') + ex_msg
    except SearchIndexError as e:
        try:
            exc_str = text_type(repr(e.args))
        except Exception:  # We don't like bare excepts
            exc_str = text_type(str(e))
        status_code = 500
        abort_message = _(u'Unable to add package to search index.') + exc_str

    if status_code != 200:
        return _abort(save_type, status_code, abort_message)

    return _prepare_and_render(save_type=save_type, data=dataset_dict, errors=errors,
                                    error_summary=error_summary)


def _prepare_and_render(save_type='', data=None, errors=None, error_summary=None):

    save_type = save_type if save_type else ''

    analytics_dict = analytics.generate_analytics_data(data)

    template_data = {
        'data': data,
        'analytics': analytics_dict,
        'errors': errors,
        'error_summary': error_summary,
        'aborted': False
    }

    if '-json' in save_type:
        body = json.dumps(template_data)
        headers = {
            'Content-Type': CONTENT_TYPES['json'],
        }
        response = make_response((body, 200, headers))
        return response
    else:
        return render('contribute_flow/create_edit.html', extra_vars=template_data)


def _abort(save_type, status_code, message):
    if '-json' in save_type:
        response_data = {
            'aborted': True,
            'message': message,
            'status_code': status_code
        }
        body = json.dumps(response_data)
        headers = {
            'Content-Type': CONTENT_TYPES['json'],
        }
        response = make_response((body, 200, headers))
        return response
    else:
        return abort(status_code, message)


def _save_or_update(context, package_type=None):
    data_dict = {}
    try:
        data_dict = _prepare_data_for_saving(context, package_type)
        pkg_dict = {}
        if data_dict.get('id'):
            # we allow partial updates to not destroy existing resources
            is_req_type = False
            if data_dict.get('private', 'True') == 'False' and data_dict.get('is_requestdata_type',
                                                                             'False') == 'True':
                context['allow_partial_update'] = False
                is_req_type = True
            else:
                context['allow_partial_update'] = True
            pkg_old = _get_action('package_show')(context, {'id': data_dict.get('id')})
            pkg_dict = _get_action('package_update')(context, data_dict)
            if is_req_type:
                for res in pkg_old.get('resources'):
                    _get_action('resource_delete')(context, {'id': res.get('id')})
        else:
            pkg_dict = _get_action('package_create')(context, data_dict)

        return pkg_dict, {}, {}

    except ValidationError as e:
        return data_dict, e.error_dict, e.error_summary


def validate(package_type=None):
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author, 'auth_user_obj': g.userobj,
               'save': 'save' in request.params}
    data_dict = {}
    save_type = request.form.get('save')
    try:
        data_dict = _prepare_data_for_saving(context, package_type)
        # data_dict = self.process_resources(data_dict)

        data_dict['batch'] = 'FAKE_ORG_BATCH_FOR_VALIDATION'
        pkg_dict = _get_action('package_validate')(context, data_dict)
        return _prepare_and_render(save_type=save_type, data=data_dict, errors={},
                                        error_summary={})

    except ValidationError as e:
        error_summary = dict(e.error_summary)
        if 'Resources' in e.error_summary:
            error_summary['Resources'] = {
                _('Resource {}').format(idx): {key: '; '.join(val)
                                               for key, val in err_dict.items()}
                for idx, err_dict in enumerate(e.error_dict.get('resources', ())) if err_dict
            }
        return _prepare_and_render(save_type=save_type, data=data_dict, errors=e.error_dict,
                                        error_summary=error_summary)
    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        return _prepare_and_render(save_type=save_type, data=data_dict, errors={},
                                        error_summary={'General Error': ex_msg})


def _prepare_data_for_saving(context, package_type):
    data_dict = clean_dict(dict_fns.unflatten(
        tuplize_dict(parse_params(request.form))))
    data_dict['type'] = package_type or data_dict.get('type')

    del data_dict['save']

    context['message'] = data_dict.get('log_message', '')

    write_logic = ContributeFlowWriteLogic(data_dict)
    write_logic.process_all(g.user)

    return data_dict


hdx_contribute.add_url_rule(u'/new', view_func=new, methods=[u'GET', u'POST'])
hdx_contribute.add_url_rule(u'/edit/<id>', view_func=edit, methods=[u'GET', u'POST'])
hdx_contribute.add_url_rule(u'/validate', view_func=validate, methods=[u'POST'])
