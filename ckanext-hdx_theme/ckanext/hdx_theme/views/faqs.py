from flask import Blueprint
import ckan.plugins.toolkit as tk
from ckan.common import c
from ckan.common import config
import ckanext.hdx_theme.helpers.faq_wordpress as fw
render = tk.render
ValidationError = tk.ValidationError
hdx_faqs = Blueprint(u'hdx_faqs', __name__, url_prefix=u'/faqs')

def read(category):
    fullname = c.userobj.display_name if c.userobj and c.userobj.display_name is not None else ''
    email = c.userobj.email if c.userobj and c.userobj.email is not None else ''
    wp_category_terms = config.get('hdx.wordpress.category.' + category)
    data = fw.faq_for_category(wp_category_terms)
    template_data = {
        'data': {
            'faq_data': data['faq_data'],
            'topics': data['topics'],
            'fullname': fullname,
            'email': email,
        },
        'capcha_api_key': config.get('ckan.recaptcha.publickey'),
        'errors': '',
        'error_summary': '',
    }

    return render('faq_others/'+category+'/main.html', template_data)

hdx_faqs.add_url_rule(u'/<category>', view_func=read)
