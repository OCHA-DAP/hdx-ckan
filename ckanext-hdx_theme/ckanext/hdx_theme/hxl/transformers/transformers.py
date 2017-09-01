import json

from ckanext.hdx_theme.hxl.operations.operations import FilterWithOperation


class BasicTransformer(object):

    def build_recipes(self):
        pass

    def generateJsonFromRecipes(self):
        return json.dumps(self.build_recipes(), default=lambda o: o.__dict__)


class FilterTransformer(BasicTransformer):

    def __init__(self, column, value):
        '''

        :param column:
        :type column: str
        :param value:
        :type value: str
        '''
        self.column = column
        self.value = value

    def build_recipes(self):
        operation = FilterWithOperation(self.column, self.value)

        return [operation.recipe]
