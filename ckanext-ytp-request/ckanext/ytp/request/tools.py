from sqlalchemy.sql.expression import or_
from ckan import model
from ckan.common import c


def get_user_member(organization_id, state=None):
    """ Helper function to get member states """
    state_query = None
    if not state:
        state_query = or_(model.Member.state == 'active', model.Member.state == 'pending')
    else:
        state_query = or_(model.Member.state == state)

    query = model.Session.query(model.Member).filter(state_query) \
        .filter(model.Member.table_name == 'user').filter(model.Member.group_id == organization_id).filter(model.Member.table_id == c.userobj.id)
    return query.first()


def get_organization_admins(group_id):
    admins = set(model.Session.query(model.User).join(model.Member, model.User.id == model.Member.table_id).
                 filter(model.Member.table_name == "user").filter(model.Member.group_id == group_id).
                 filter(model.Member.state == 'active').filter(model.Member.capacity == 'admin'))

    admins.update(set(model.Session.query(model.User).filter(model.User.sysadmin == True)))  # noqa

    return admins


def get_ckan_admins():
    admins = set(model.Session.query(model.User).filter(model.User.sysadmin == True))  # noqa

    return admins
