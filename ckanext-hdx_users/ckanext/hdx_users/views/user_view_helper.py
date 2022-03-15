import json

import ckan.lib.navl.dictization_functions as dictization_functions
from ckan.plugins import toolkit as tk

_ = tk._
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
DataError = dictization_functions.DataError
CaptchaNotValid = _('Captcha is not valid')
OnbCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})
OnbNotAuth = json.dumps({'success': False, 'error': {'message': _('Unauthorized to create user')}})
OnbTokenNotFound = json.dumps({'success': False, 'error': {'message': 'Token not found'}})
OnbIntegrityErr = json.dumps({'success': False, 'error': {'message': 'Integrity Error'}})
OnbSuccess = json.dumps({'success': True})
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbExistingUsername = json.dumps({'success': False, 'error': {'message': 'Username is already used'}})
OnbErr = json.dumps({'success': False, 'error': {'message': _('Something went wrong. Please contact support.')}})
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})


def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})
