import logging

from botocore.exceptions import ClientError

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_search.helpers.qa_s3 import LogS3
from ckanext.s3filestore.helpers import generate_temporary_link

_ = tk._
g = tk.g
check_access = tk.check_access
abort = tk.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized

log = logging.getLogger(__name__)


class QALogsLogic(object):

    def __init__(self, resource_id, log_filename):
        super(QALogsLogic, self).__init__()
        self.resource_id = resource_id
        self.log_filename = log_filename

        self.url = None

    def read(self):
        self.url = self._get_url_to_qa_log(self.resource_id, self.log_filename)
        return self

    def _get_url_to_qa_log(self, resource_id, log_filename, path_format='resources/{resource_id}/{log_filename}'):
        try:
            context = {'model': model, 'user': g.user,
                       'auth_user_obj': g.userobj}
            check_access('qa_dashboard_show', context)
        except (NotFound, NotAuthorized):
            abort(404, _('Not authorized to see this page'))
        try:
            path = path_format.format(resource_id=resource_id, log_filename=log_filename)
            uploader = LogS3()
            s3 = uploader.get_s3_session()
            client = s3.client(service_name='s3', endpoint_url=uploader.host_name)
            # url = client.generate_presigned_url(ClientMethod='get_object',
            #                                     Params={'Bucket': uploader.bucket_name,
            #                                             'Key': path},
            #                                     ExpiresIn=60)
            url = generate_temporary_link(client, uploader.bucket_name, path)
            return url

        except ClientError as ex:
            log.error(str(ex))
