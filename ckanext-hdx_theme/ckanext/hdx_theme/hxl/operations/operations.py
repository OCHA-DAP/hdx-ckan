from ckanext.hdx_theme.hxl.operations.recipes import WithRowsRecipe


class BasicOperation(object):
    def __init__(self, recipe):
        '''
        :param recipe:
        :type recipe: ckanext.hdx_theme.hxl.operations.recipes.BasicRecipe
        '''
        self.recipe = recipe


class FilterWithOperation(BasicOperation):
    def __init__(self, column, value):
        query = '{}={}'.format(column, value)
        recipe = WithRowsRecipe([query])
        super(FilterWithOperation, self).__init__(recipe)