import ckan.model as model

downloadable_formats = {
    'csv', 'xls', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False

def get_last_modifier_user(package_id):
    pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
    pkg = pkg_list[0]
    rev_id = pkg.latest_related_revision.id
    act_list = model.Session.query(model.Activity).filter(model.Activity.revision_id == rev_id).all()
    act = act_list[0]
    usr_id = act.user_id
    return model.User.get(usr_id)