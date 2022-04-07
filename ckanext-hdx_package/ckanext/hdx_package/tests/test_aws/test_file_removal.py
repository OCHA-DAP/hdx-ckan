# encoding: utf-8

import pytest
import os
import six

from werkzeug.datastructures import FileStorage

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_package.tests.test_aws.hdx_s3_test_base import HDXS3TestBase

config = tk.config
_get_action = tk.get_action


class TestFileRemovalS3(HDXS3TestBase):

    def test_resource_delete(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']
        assert self.__file_exists(resource_id, self.file1_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file1_name)

    def test_resource_update(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self._resource_update_with_upload(context, self.file2_name, self.file2_name, resource_id)
        assert not self.__file_exists(resource_id, self.file1_name)
        assert self.__file_exists(resource_id, self.file2_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file2_name)

    def test_resource_update_with_same_resource_name(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self._resource_update_with_upload(context, self.file2_name, 'Test resource1.csv', resource_id)
        assert not self.__file_exists(resource_id, self.file1_name)
        assert self.__file_exists(resource_id, self.file2_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file2_name)

    def test_resource_update_with_same_file_name(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']

        resource_dict2 = self._resource_update_with_upload(context, self.file1_name, 'Test resource2.csv', resource_id)
        assert self.__file_exists(resource_id, self.file1_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file1_name)

    def test_resource_update_with_special_chars(self):

        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        resource_dict = self._resource_create_with_upload(context, self.file1_name, u'Annual data for Côte d\'Ivoire',
                                                           self.dataset1_name)

        resource_id = resource_dict['id']
        assert self.__file_exists(resource_id, self.file1_name)

        self._resource_update_with_upload(context, self.file2_name, u'Annual data for Côte d\'Ivoire 2', resource_id)
        assert not self.__file_exists(resource_id, self.file1_name)
        assert self.__file_exists(resource_id, self.file2_name)

        _get_action('resource_delete')(context, {'id': resource_id})
        assert not self.__file_exists(resource_id, self.file2_name)

    def test_package_purge(self):
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._create_package_by_user(self.dataset2_name, 'testsysadmin', create_org_and_group=False)
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.dataset2_name)

        resource_id = resource_dict['id']

        _get_action('hdx_dataset_purge')(context, {'id': self.dataset2_name})
        assert not self.__file_exists(resource_id, self.file1_name)

    def test_package_revise(self):
        context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        self._create_package_by_user(self.revise_dataset_name, 'testsysadmin', create_org_and_group=False)
        resource_dict = self._resource_create_with_upload(context, self.file1_name, 'Test resource1.csv',
                                                           self.revise_dataset_name)
        resource_id = resource_dict['id']
        file_path = os.path.join(os.path.dirname(__file__), self.file2_name)
        with open(file_path) as f:
            file_upload = FileStorage(f)
            package_dict = _get_action('package_revise')(context,
                                                         {
                                                             'match__name': self.revise_dataset_name,
                                                             'update__resources__1__name': 'Test resource2.csv',
                                                             'update__resources__1__upload': file_upload,

                                                         })
            assert not self.__file_exists(resource_id, self.file1_name)
            assert self.__file_exists(resource_id, self.file2_name)

        _get_action('hdx_dataset_purge')(context, {'id': self.revise_dataset_name})
        assert not self.__file_exists(resource_id, self.file2_name)

    @classmethod
    def __file_exists(cls, resource_id, file_name):
        return bool(cls._fetch_s3_object(resource_id, file_name))
