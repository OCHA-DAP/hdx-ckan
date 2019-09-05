import ckan.lib.helpers as h
import ckan.authz as authz
import ckan.model as model

from ckan.logic import NotFound
from ckan.common import g
from ckanext.hdx_users.helpers.notifications_dao import MembershipRequestsDao, RequestDataDao


def get_notification_service():
    if not g.user:
        raise NotFound('Seems like user is not logged in so no notification service can be created')
    userobj = model.User.get(g.user)
    is_sysadmin = authz.is_sysadmin(g.user)
    membership_request_dao = MembershipRequestsDao(model, userobj, is_sysadmin)
    request_data_dao = RequestDataDao(model, userobj, is_sysadmin)

    membership_request_service = MembershipRequestsService(membership_request_dao, is_sysadmin)
    request_data_service = SysadminRequestDataService(request_data_dao, g.user) \
        if is_sysadmin else RequestDataService(request_data_dao, g.user)

    notification_service = NotificationService(membership_request_service, request_data_service, is_sysadmin)
    return notification_service


class NotificationService(object):

    def __init__(self, membership_request_service, request_data_service, is_sysadmin):
        '''
        :param membership_request_service:
        :type membership_request_service: MembershipRequestsService
        :param request_data_service:
        :type request_data_service: RequestDataService
        '''
        self.request_data_service = request_data_service
        self.membership_request_service = membership_request_service
        self.is_sysadmin = is_sysadmin

    def get_notifications(self):
        notifications = self.membership_request_service.get_org_membership_requests() \
                        + self.request_data_service.get_requestdata_requests()

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
