import logging

from ckanext.s3filestore.uploader import BaseS3Uploader

import ckan.plugins.toolkit as tk

config = tk.config

log = logging.getLogger(__name__)


class LogS3(BaseS3Uploader):

    def get_s3_bucket(self, bucket_name):
        self.bucket_name = config.get('ckanext.s3filestore.aws_bucket_name', 'hdx-ckan-filestore-dev') + '-log'
        return super(LogS3, self).get_s3_bucket(bucket_name)
