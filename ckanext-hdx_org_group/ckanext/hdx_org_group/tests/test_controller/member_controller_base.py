import unicodedata


class MemberControllerBase(object):

    def _get_url(self, app, url, apitoken=None):

        if apitoken:
            page = app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apitoken).encode('ascii', 'ignore')},
                           follow_redirects=True)
        else:
            page = app.get(url)
        return page

    def _post_url(self, app, url, apitoken=None):

        if apitoken:
            page = app.post(url, headers={
                'Authorization': unicodedata.normalize('NFKD', apitoken).encode('ascii', 'ignore')},
                            follow_redirects=True)
        else:
            page = app.post(url)
        return page
