import ckan.lib.helpers as h
import ckan.authz as authz
import ckan.model as model

from ckan.logic import NotFound
from ckan.common import g

from ckanext.hdx_users.helpers.notifications_dao import MembershipRequestsDao, RequestDataDao, ExpiredDatasetsDao,\
    QuarantinedDatasetsDao
from ckanext.hdx_package.helpers.freshness_calculator import FreshnessCalculator,\
    UPDATE_STATUS_URL_FILTER, UPDATE_STATUS_UNKNOWN, UPDATE_STATUS_FRESH, UPDATE_STATUS_NEEDS_UPDATE


def get_notification_service():
    if not g.user:
        raise NotFound('Seems like user is not logged in so no notification service can be created')
    userobj = model.User.get(g.user)
    is_sysadmin = authz.is_sysadmin(g.user)

    membership_request_dao = MembershipRequestsDao(model, userobj, is_sysadmin)
    request_data_dao = RequestDataDao(model, userobj, is_sysadmin)
    expired_datasets_dao = ExpiredDatasetsDao(userobj, is_sysadmin)
    quarantined_datasets_dao = QuarantinedDatasetsDao(model, userobj, is_sysadmin)

    membership_request_service = MembershipRequestsService(membership_request_dao, is_sysadmin)
    request_data_service = SysadminRequestDataService(request_data_dao, g.user) \
        if is_sysadmin else RequestDataService(request_data_dao, g.user)
    expired_datasets_service = ExpiredDatasetsService(expired_datasets_dao, userobj, is_sysadmin)

    quarantine_service = SysadminQuarantinedDatasetsService(quarantined_datasets_dao, g.user) \
        if is_sysadmin else QuarantinedDatasetsService(quarantined_datasets_dao, g.user)

    notification_service = NotificationService(membership_request_service, request_data_service,
                                               expired_datasets_service, quarantine_service,
                                               is_sysadmin)
    return notification_service


class NotificationService(object):

    def __init__(self, membership_request_service, request_data_service, expired_datasets_service,
                 quarantined_datasets_service,
                 is_sysadmin):
        '''
        :param membership_request_service:
        :type membership_request_service: MembershipRequestsService
        :param request_data_service:
        :type request_data_service: RequestDataService
        :param expired_datasets_service:
        :type expired_datasets_service: ExpiredDatasetsService
        :param quarantined_datasets_service:
        :type quarantined_datasets_service: QuarantinedDatasetsService
        :param is_sysadmin:
        :type is_sysadmin: bool
        '''

        self.request_data_service = request_data_service
        self.membership_request_service = membership_request_service
        self.expired_dataset_service = expired_datasets_service
        self.quarantined_datasets_service = quarantined_datasets_service
        self.is_sysadmin = is_sysadmin

    def get_notifications(self):
        notifications = self.membership_request_service.get_org_membership_requests() \
                        + self.request_data_service.get_requestdata_requests() \
                        + self.expired_dataset_service.get_expired_datasets_info() \
                        + self.quarantined_datasets_service.get_quarantined_datasets_info()

        notifications.sort(key=lambda n: n.get('last_date'), reverse=True)
        any_personal_notifications = False
        for notification in notifications:
            notification['last_date'] = notification.get('last_date').strftime('%b %-d, %Y') \
                if notification.get('last_date') else ''
            if not any_personal_notifications and not notification['for_sysadmin']:
                any_personal_notifications = True


        return {
            'any_personal_notifications': any_personal_notifications,
            'count': len(notifications),
            'list': notifications,
            'is_sysadmin': self.is_sysadmin
        }


class MembershipRequestsService(object):
    def __init__(self, membership_requests_dao, is_sysadmin):
        '''
        :param membership_requests_dao:
        :type membership_requests_dao: MembershipRequestsDao
        :param is_sysadmin:
        :type is_sysadmin: bool
        '''
        self.membership_request_dao = membership_requests_dao
        self.is_sysadmin = is_sysadmin

    def get_org_membership_requests(self):
        requests_grouped_by_org = self.membership_request_dao.fetch_membership_requests_with_org_info()
        if self.is_sysadmin:
            org_names_where_user_is_admin = self.membership_request_dao.fetch_org_names_where_user_is_admin()
            org_names_where_user_is_admin = set(
                (o.name for o in org_names_where_user_is_admin)) if org_names_where_user_is_admin else set()
        else:
            org_names_where_user_is_admin = set()
        notifications = []

        if requests_grouped_by_org:
            for request in requests_grouped_by_org:
                notifications.append(
                    {
                        'org_title': request.title,
                        'org_name': request.name,
                        'org_hdx_url': h.url_for('organization_members', id=request.name),
                        'html_template': 'light/notifications/org_membership_snippet.html',
                        'last_date': request.last_date,
                        'count': request.count,
                        'for_sysadmin': request.name not in org_names_where_user_is_admin
                                            if self.is_sysadmin else False,
                        'is_sysadmin': self.is_sysadmin
                    }
                )

        return notifications


class RequestDataService(object):

    def __init__(self, request_data_dao, username):
        '''
        :param request_data_dao:
        :type request_data_dao: RequestDataDao
        :param username: the username of the current user
        :type username: str
        '''
        self.request_data_dao = request_data_dao
        self.username = username
        self.is_sysadmin = False

    def get_requestdata_requests(self):
        notifications = []
        data_requests = self.request_data_dao.fetch_requestdata_requests()
        if data_requests and data_requests[0].count:
            notifications.append(
                {
                    'last_date': data_requests[0].last_date,
                    'count': data_requests[0].count,
                    'html_template': 'light/notifications/requestdata_snippet.html',
                    'my_requests_url': h.url_for('requestdata_my_requests', id=self.username),
                    'for_sysadmin': False,
                    'is_sysadmin': self.is_sysadmin

                }
            )
        return notifications


class SysadminRequestDataService(RequestDataService):

    def __init__(self, request_data_dao, username):
        super(SysadminRequestDataService, self).__init__(request_data_dao, username)
        self.is_sysadmin = True

    def get_requestdata_requests(self):
        notifications = super(SysadminRequestDataService, self).get_requestdata_requests()
        sysadmin_requests = self.request_data_dao.fetch_requestdata_requests_for_sysadmins()
        for request in sysadmin_requests:
            notifications.append(
                {
                    'last_date': request.last_date,
                    'count': request.count,
                    'html_template': 'light/notifications/requestdata_snippet.html',
                    'my_requests_url': h.url_for('requestdata_organization_requests', id=request.name),
                    'org_title': request.title,
                    'org_name': request.name,
                    'for_sysadmin': True,
                    'is_sysadmin': self.is_sysadmin

                }
            )
        return notifications


class ExpiredDatasetsService(object):
    def __init__(self, expired_datasets_dao, username, is_sysadmin):
        '''
        :param expired_datasets_dao:
        :type expired_datasets_dao: ExpiredDatasetsDao
        :param username: the username of the current user
        :type username: str
        '''

        self.expired_datasets_dao = expired_datasets_dao
        self.username = username
        self.is_sysadmin = is_sysadmin

    def get_expired_datasets_info(self):
        count, last_date = self.expired_datasets_dao.fetch_expired_datasets()
        notifications = []
        if count > 0:
            param_dict = {
                UPDATE_STATUS_URL_FILTER: UPDATE_STATUS_NEEDS_UPDATE
            }
            notifications.append(
                {
                    'last_date': last_date,
                    'count': count,
                    'html_template': 'light/notifications/expired_datasets_snippet.html',
                    'my_dashboard_url': h.url_for('user_dashboard_datasets', **param_dict),
                    'for_sysadmin': False,
                    'is_sysadmin': self.is_sysadmin
                }
            )
        return notifications


class QuarantinedDatasetsService(object):
    def __init__(self, quarantined_datasets_dao, username):
        '''
        :param quarantined_datasets_dao:
        :type quarantined_datasets_dao: QuarantinedDatasetsDao
        :param username: the username of the current user
        :type username: str
        :param is_sysadmin:
        :type is_sysadmin: bool
        '''

        self.quarantined_datasets_dao = quarantined_datasets_dao
        self.username = username
        self.is_sysadmin = False

    def get_quarantined_datasets_info(self):
        dataset_list, count = self.quarantined_datasets_dao.fetch_quarantined_datasets_for_user()
        notifications = []
        self._add_notifications(notifications, dataset_list, False)
        return notifications

    def _add_notifications(self, notifications, dataset_list, for_sysadmin):
        if dataset_list:
            for dataset in dataset_list:
                notifications.append(
                    {
                        'last_date': dataset.get('last_date'),
                        'html_template': 'light/notifications/quarantined_datasets_snippet.html',
                        'dataset': dataset,
                        'dataset_url': h.url_for(controller='package', action='read', id=dataset.get('name')),
                        'for_sysadmin': for_sysadmin,
                        'is_sysadmin': self.is_sysadmin
                    }
                )


class SysadminQuarantinedDatasetsService(QuarantinedDatasetsService):
    def __init__(self, quarantined_datasets_dao, username):
        '''
        :param quarantined_datasets_dao:
        :type quarantined_datasets_dao: QuarantinedDatasetsDao
        :param username: the username of the current user
        :type username: str
        '''
        super(SysadminQuarantinedDatasetsService, self).__init__(quarantined_datasets_dao, username)
        self.is_sysadmin = True

    def get_quarantined_datasets_info(self):
        notifications = super(SysadminQuarantinedDatasetsService, self).get_quarantined_datasets_info()
        dataset_list, count = self.quarantined_datasets_dao.fetch_all_quarantined_datasets()
        self._add_notifications(notifications, dataset_list, True)
        return notifications
