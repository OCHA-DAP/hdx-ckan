import logging
import unicodedata

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

from collections import namedtuple
from ckanext.hdx_org_group.helpers.static_lists import ORGANIZATION_TYPE_LIST

log = logging.getLogger(__name__)

url_for = tk.url_for

Member = namedtuple('Member', ['name', 'capacity'])

MEMBERS = [
    Member('member_user1', 'member'),
    Member('editor_user1', 'editor'),
    Member('admin_user1', 'admin'),
]

ORG = 'org-for-testing-members-page'


class TestMembersPageAuth(hdx_test_base.HdxBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestMembersPageAuth, cls).setup_class()
        for member in MEMBERS:
            factories.User(name=member.name, email='{}@hdx.hdxtest.org'.format(member.name),
                           apikey='{}_apikey'.format(member.name))
        for member in MEMBERS:
            user = model.User.by_name(member.name)
            user.apikey = member.name + '_apikey'
        model.Session.commit()

        factories.Organization(
            name=ORG,
            title='ORG NAME FOR TESTING MEMBERS PAGE',
            users=[m._asdict() for m in MEMBERS],
            hdx_org_type=ORGANIZATION_TYPE_LIST[0][1],
            org_url='https://hdx.hdxtest.org/'
        )

    def test_member_page_load(self):
        for member in MEMBERS:
            url = url_for('hdx_members.members', id=ORG)
            user = model.User.by_name(member.name)
            result = self.app.get(url, headers={
                'Authorization': unicodedata.normalize('NFKD', user.apikey).encode('ascii', 'ignore')
            })
            assert 200 == result.status_code, 'HTTP OK for {}'.format(member.name)
            assert 'server error' not in str(result.body).lower()
