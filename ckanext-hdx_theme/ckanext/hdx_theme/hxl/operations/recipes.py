import json

class BasicRecipe(object):
    def __init__(self, filter):
        self.filter = filter

    def to_json(self):
        return json.dumps(self)


class WithRowsRecipe(BasicRecipe):
    def __init__(self, queries):
        '''
        :param queries: list of conditions like "date+year>2010"
        :type queries: list[str]
        '''

        super(WithRowsRecipe, self).__init__('with_rows')
        self.queries = queries