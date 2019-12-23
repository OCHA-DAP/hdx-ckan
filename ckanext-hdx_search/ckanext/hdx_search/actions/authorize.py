from ckan.common import _

def hdx_qa_dashboard_show(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins/qa officers can view the qa dashboard')}


def hdx_qa_sdcmicro_run(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can run the sdc micro check')}
