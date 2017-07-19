import sys

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

        try:
            self.__inner_dict = {}
            if field_list and src_dict:
                for field in field_list:
                    self.__inner_dict[field] = src_dict.get(field)
            else:
                raise HashGenerationException('Either field list or source dict are null')
        except Exception, e:
            raise HashGenerationException('Exception while trying to generate hash code'), None, sys.exc_info()[2]

    def compute_hash(self):
        return hash(frozenset(self.__inner_dict.items()))


class HashGenerationException(Exception):
    type = 'hashing-generation'

    def __init__(self, message, exceptions=[]):

        super(Exception, self).__init__(message)

        self.errors = exceptions
