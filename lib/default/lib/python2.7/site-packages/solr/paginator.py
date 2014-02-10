import math

class SolrPaginator:
    """
    Create a Django-like Paginator for a solr response object. Can be handy
    when you want to hand off a Paginator and/or Page to a template to
    display results, and provide links to next page, etc.

    For example:
    >>> from solr import SolrConnection, SolrPaginator
    >>>
    >>> conn = SolrConnection('http://localhost:8083/solr')
    >>> response = conn.query('title:huckleberry')
    >>> paginator = SolrPaginator(response)
    >>> print paginator.num_pages
    >>> page = paginator.get_page(5)

    For more details see the Django Paginator documentation and solrpy
    unittests.

      http://docs.djangoproject.com/en/dev/topics/pagination/

    """

    def __init__(self, result, default_page_size=None):
        self.params = result.header['params']
        self.result = result
        self.query = result._query

        if 'rows' in self.params:
            self.page_size = int(self.params['rows'])
        elif default_page_size:
            try:
                self.page_size = int(default_page_size)
            except ValueError:
                raise ValueError('default_page_size must be an integer')

            if self.page_size < len(self.result.results):
                raise ValueError('Invalid default_page_size specified, lower '
                                 'than number of results')

        else:
            self.page_size = len(self.result.results)

    @property
    def count(self):
        return int(self.result.numFound)

    @property
    def num_pages(self):
        if self.count == 0:
            return 0
        return int(math.ceil(float(self.count) / float(self.page_size)))

    @property
    def page_range(self):
        """List the index numbers of the available result pages."""
        if self.count == 0:
            return []
        # Add one because range is right-side exclusive
        return range(1, self.num_pages + 1)

    def _fetch_page(self, start=0):
        """Retrieve a new result response from Solr."""
        # need to convert the keys to strings to pass them as parameters
        new_params = {}
        for k, v in self.params.items():
            new_params[str(k)] = v.encode('utf-8')

        # get the new start index
        new_params['start'] = start
        return self.query(**new_params)

    def page(self, page_num=1):
        """Return the requested Page object"""
        try:
            int(page_num)
        except:
            raise 'PageNotAnInteger'

        if page_num not in self.page_range:
            raise 'EmptyPage', 'That page does not exist.'

        # Page 1 starts at 0; take one off before calculating
        start = (page_num - 1) * self.page_size
        new_result = self._fetch_page(start=start)
        return SolrPage(new_result.results, page_num, self)


class SolrPage:
    """A single Paginator-style page."""

    def __init__(self, result, page_num, paginator):
        self.result = result
        self.number = page_num
        self.paginator = paginator

    @property
    def object_list(self):
        return self.result

    def has_next(self):
        if self.number < self.paginator.num_pages:
            return True
        return False

    def has_previous(self):
        if self.number > 1:
            return True
        return False

    def has_other_pages(self):
        if self.paginator.num_pages > 1:
            return True
        return False

    def start_index(self):
        # off by one because self.number is 1-based w/django,
        # but start is 0-based in solr
        return (self.number - 1) * self.paginator.page_size

    def end_index(self):
        # off by one because we want the last one in this set,
        # not the next after that, to match django paginator
        return self.start_index() + len(self.result) - 1

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1

