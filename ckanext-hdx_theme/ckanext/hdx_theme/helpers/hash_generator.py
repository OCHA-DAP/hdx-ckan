import hashlib
import logging

from ckanext.hdx_theme.helpers.exception import BaseHdxException

log = logging.getLogger(__name__)


def generate_hash_dict(src_dict_list, dict_identifier, field_list):
    '''
    Works only on simple dictionaries (not nested). At least the specified fields need to not be nested.

    :param src_dict_list: for each dict in this list a hash code will be computed
    :type src_dict_list: list[dict]
    :param dict_identifier: field that uniquely identifies a dict in the src_dict_list (ex 'id')
    :type dict_identifier: str
    :param field_list: list of fields in the dict that will be taken into consideration when computing the hash code
    :type field_list: list[str]
    :return: a map of identifiers to hash codes
    :rtype: dict[str, int]
    '''
    return {src_dict[dict_identifier]: HashCodeGenerator(src_dict, field_list).compute_hash()
            for src_dict in src_dict_list if dict_identifier in src_dict}


class HashCodeGenerator(object):
    '''
    Works only on simple dictionaries (not nested). At least the specified fields need to not be nested.
    '''
    def __init__(self, src_dict, field_list=None):
        '''
        :param src_dict: for each dict in this list a hash code will be computed
        :type src_dict: dict
        :param field_list: list of fields in the dict that will be taken into consideration when computing the hash code
        :type field_list: list[str]
        '''

        if not field_list and src_dict:
            field_list = list(src_dict.keys())

        field_list.sort()
        try:
            self.__inner_string = ''
            if field_list and src_dict:
                for field in field_list:
                    self.__inner_string += '{}-{},'.format(field, src_dict.get(field))
            else:
                raise HashGenerationException('Either field list or source dict are null')
        except Exception as e:
            raise HashGenerationException('Exception while trying to generate hash code')

    def compute_hash(self):
        hash_builder = hashlib.md5()
        hash_builder.update(self.__inner_string.encode())
        hash_code = hash_builder.hexdigest()
        log.info('Generated code for {} is {}'.format(self.__inner_string, hash_code))
        return hash_code


class HashGenerationException(BaseHdxException):
    type = 'hashing-generation'
