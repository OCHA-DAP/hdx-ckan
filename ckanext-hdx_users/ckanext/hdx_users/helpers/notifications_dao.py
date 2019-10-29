import datetime
import dateutil.parser

from sqlalchemy import func

import ckan.model as ckan_model
import ckan.plugins.toolkit as tk

import ckanext.requestdata.model as requestdata_model

get_action = tk.get_action


class MembershipRequestsDao(object):
    def __init__(self, model, userobj, is_sysadmin):
        '''
        :param model:
        :type model: ckan_model
        :param userobj:
        :type userobj: ckan_model.User
        :param is_sysadmin:
        :type is_sysadmin: bool
        '''

        self.is_sysadmin = is_sysadmin
        self.userobj = userobj
        self.model = model if model else ckan_model

    def fetch_membership_requests_with_org_info(self):

        model = self.model

        query = model.Session.query(model.Group.name, model.Group.title,
                                    func.count(model.Member.id).label('count'),
                                    func.max(model.MemberRevision.revision_timestamp).label('last_date')) \
            .filter(model.Member.group_id == model.Group.id) \
            .filter(model.Group.state == 'active') \
            .filter(model.Member.revision_id == model.MemberRevision.revision_id) \
            .filter(model.Member.table_name == "user") \
            .filter(model.Member.state == 'pending')

        if not self.is_sysadmin:
            admin_in_groups = model.Session.query(model.Member) \
                .filter(model.Member.state == "active") \
                .filter(model.Member.table_name == "user") \
                .filter(model.Member.capacity == 'admin') \
                .filter(model.Member.table_id == self.userobj.id)

            if admin_in_groups.count() <= 0:
                return []

            query = query.filter(model.Member.group_id.in_(admin_in_groups.values(model.Member.group_id)))

        query = query.group_by(model.Group.name, model.Group.title)

        return query.all()

    def fetch_org_names_where_user_is_admin(self):
        model = self.model

        admin_in_groups = model.Session.query(model.Group.name) \
            .filter(model.Member.group_id == model.Group.id) \
            .filter(model.Group.state == 'active') \
            .filter(model.Group.type == 'organization') \
            .filter(model.Member.state == 'active') \
            .filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity == 'admin') \
            .filter(model.Member.table_id == self.userobj.id)

        return admin_in_groups.all()


class RequestDataDao(object):
    def __init__(self, model, userobj, is_sysadmin):

        self.is_sysadmin = is_sysadmin
        self.userobj = userobj
        self.model = model if model else ckan_model

    def fetch_requestdata_requests(self):
        model = self.model

        query = model.Session.query(func.max(requestdata_model.ckanextRequestdata.modified_at).label('last_date'),
                                    func.count(requestdata_model.ckanextRequestdata.id).label('count')) \
            .filter(requestdata_model.ckanextRequestdata.package_id == model.Package.id) \
            .filter(requestdata_model.ckanextRequestdata.state == 'new') \
            .filter(model.Package.state == 'active') \
            .filter(model.Package.maintainer == self.userobj.id)

        return query.all()

    def fetch_requestdata_requests_for_sysadmins(self):
        model = self.model

        if self.is_sysadmin:
            query = model.Session.query(model.Group.name, model.Group.title,
                                        func.max(requestdata_model.ckanextRequestdata.modified_at).label('last_date'),
                                        func.count(requestdata_model.ckanextRequestdata.id).label('count')) \
                .filter(model.Package.owner_org == model.Group.id) \
                .filter(model.Group.state == 'active') \
                .filter(requestdata_model.ckanextRequestdata.package_id == model.Package.id) \
                .filter(requestdata_model.ckanextRequestdata.state == 'new') \
                .filter(model.Package.state == 'active') \
                .group_by(model.Group.name, model.Group.title)

            return query.all()

        return []


class ExpiredDatasetsDao(object):
    def __init__(self, userobj, is_sysadmin):

        self.is_sysadmin = is_sysadmin
        self.userobj = userobj

    def fetch_expired_datasets(self):
        now = datetime.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        now_date_for_solr = now.isoformat() + 'Z'

        query_string = '(maintainer:{} AND {}:[* TO {}])'.format(self.userobj.id, 'due_date', now_date_for_solr)
        query_params = {
            'include_private': True,
            'start': 0,
            'rows': 10,
            'sort': 'due_date desc',
            'fq': query_string
        }
        search_result = get_action('package_search')({}, query_params)
        num_of_datasets = search_result.get('count', 0)

        last_date = None
        if num_of_datasets > 0:
            last_date_str = search_result['results'][0].get('due_date')
            last_date = dateutil.parser.parse(last_date_str[0:-1])

        return num_of_datasets, last_date
