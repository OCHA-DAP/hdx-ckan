import ckan.model as model

def populate_mock_as_c(mock_c, username):
    mock_c.user = username
    mock_c.userobj = model.User.by_name(username)