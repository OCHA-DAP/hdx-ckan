from identification import OpenIdIdentificationPlugin

def make_identification_plugin(store='mem',
                openid_field = "openid",
                session_name = None,
                login_handler_path = None,
                logout_handler_path = None,
                login_form_url = None,
                error_field = 'error',
                logged_in_url = None,
                logged_out_url = None,
                came_from_field = 'came_from',
                store_file_path='',
                rememberer_name = None,
                sql_associations_table = '',
                sql_nonces_table = '',
                sql_connstring = '',
                ax_require = '',
                ax_optional = '',
                sreg_require = '',
                sreg_optional = ''):
    if store not in (u'mem',u'file',u'sql'):
        raise ValueError("store needs to be 'mem', 'sql' or 'file'")
    if login_form_url is None:
        raise ValueError("login_form_url needs to be given")
    if rememberer_name is None:
        raise ValueError("rememberer_name needs to be given")
    if login_handler_path is None:
        raise ValueError("login_handler_path needs to be given")
    if logout_handler_path is None:
        raise ValueError("logout_handler_path needs to be given")
    if session_name is None:
        raise ValueError("session_name needs to be given")
    if logged_in_url is None:
        raise ValueError("logged_in_url needs to be given")
    if logged_out_url is None:
        raise ValueError("logged_out_url needs to be given")

    plugin = OpenIdIdentificationPlugin(store, 
        openid_field = openid_field,
        error_field = error_field,
        session_name = session_name,
        login_form_url = login_form_url,
        login_handler_path = login_handler_path,
        logout_handler_path = logout_handler_path,
        store_file_path = store_file_path,
        logged_in_url = logged_in_url,
        logged_out_url = logged_out_url,
        came_from_field = came_from_field,
        rememberer_name = rememberer_name,
        sql_associations_table = sql_associations_table,
        sql_nonces_table = sql_nonces_table,
        sql_connstring = sql_connstring,
        ax_require = ax_require,
        ax_optional = ax_optional,
        sreg_require = sreg_require,
        sreg_optional = sreg_optional)
    return plugin

