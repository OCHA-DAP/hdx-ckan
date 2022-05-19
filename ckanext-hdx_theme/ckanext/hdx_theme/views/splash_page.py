from flask import Blueprint
from rdflib import Graph, Literal, BNode, RDF
from rdflib.namespace import Namespace

import ckan.plugins.toolkit as tk
from ckan.common import config

_ = tk._
g = tk.g
h = tk.h
check_access = tk.check_access
get_action = tk.get_action
abort = tk.abort
redirect = tk.redirect_to
render = tk.render

NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError

hdx_splash = Blueprint(u'hdx_splash', __name__)


def google_searchbox_data():
    # SCHEMA = Namespace('http://schema.org/')
    ckan_url = config.get('ckan.site_url', 'https://data.humdata.org').replace('http://', 'https://') + '/'
    search_action_url = ckan_url + 'search?q={search_term_string}'
    #
    # website_node = BNode()
    # g = Graph()
    # g.bind('schema', SCHEMA)
    # g.add((website_node, RDF.type, SCHEMA.WebSite))
    # g.add((website_node, SCHEMA.url, Literal(ckan_url)))
    # search_action = BNode()
    #
    # g.add((website_node, SCHEMA.potentialAction, search_action))
    # g.add((search_action, RDF.type, SCHEMA.SearchAction))
    # # g.add((search_action, SCHEMA.target, Literal(search_action_url)))
    # g.add((search_action, SCHEMA['query-input'], Literal('required name=search_term_string')))
    #
    # entry_point = BNode()
    # g.add((search_action, SCHEMA.target, entry_point))
    # g.add((entry_point, RDF.type, SCHEMA.EntryPoint))
    # g.add((entry_point, SCHEMA.urlTemplate, Literal(search_action_url)))
    #
    # return g.serialize(format='json-ld', auto_compact=True).decode('UTF-8')
    data = '''
    {{
      "@context": "https://schema.org",
      "@type": "WebSite",
      "url": "{ckan_url}",
      "potentialAction": {{
        "@type": "SearchAction",
        "target": {{
          "@type": "EntryPoint",
          "urlTemplate": "{search_url_template}"
        }},
        "query-input": "required name=search_term_string"
      }}
    }}
    '''.format(ckan_url=ckan_url, search_url_template=search_action_url)
    return data


structured_data = google_searchbox_data()


def index():
    if g.userobj is not None:
        site_title = config.get('ckan.site_title', 'CKAN')
        msg = None
        url = h.url_for(controller='user', action='edit')
        is_google_id = \
            g.userobj.name.startswith('https://www.google.com/accounts/o8/id')
        if not g.userobj.email and (is_google_id and not g.userobj.fullname):
            msg = _(u'Please <a href="{link}">update your profile</a>'
                    u' and add your email address and your full name. '
                    u'{site} uses your email address'
                    u' if you need to reset your password.'.format(
                link=url, site=site_title))
        elif not g.userobj.email:
            msg = _('Please <a href="%s">update your profile</a>'
                    ' and add your email address. ') % url + \
                  _('%s uses your email address'
                    ' if you need to reset your password.') \
                  % site_title
        elif is_google_id and not g.userobj.fullname:
            msg = _('Please <a href="%s">update your profile</a>'
                    ' and add your full name.') % (url)
        if msg:
            h.flash_notice(msg, allow_html=True)

    template_data = {
        'structured_data': structured_data,
        'alert_bar': {
            'title': config.get('hdx.alert_bar_title'),
            'url': config.get('hdx.alert_bar_url'),

        }
    }
    return render('home/index.html', template_data)


def about(page):
    title = {
        'license': _('Data Licenses'),
        'terms': _('Terms of Service'),
        'hdx-qa-process': _('HDX QA Process')
    }
    html = {
        'license': 'licenses',
        'terms': 'terms',
        'hdx-qa-process': 'home/snippets/qa-process.html'
    }
    templates = {
        'hdx-qa-process': 'home/about2-light.html'
    }

    title_item = title.get(page)
    if title_item is None:
        abort(404, _("The requested about page doesn't exist"))

    template = templates.get(page, 'redirect')
    if template == 'redirect':
        html_item = html.get(page)
        url = h.url_for('hdx_faqs.read', category=html_item)
        result = redirect(url)
        return result
    else:
        html_item = html.get(page)

    extra_vars = {'title': title_item, 'html': html_item, 'page': page}
    return render(template, extra_vars)


def about_hrinfo():
    from ckan.lib.base import render_jinja2
    title = {'hr_info': _('Legacy HR Info')}
    html = {'hr_info': 'home/snippets/hdx_hr_info.html'}

    title_item = title['hr_info']
    html_item = html['hr_info']

    if title_item is None:
        message = _("The requested about page doesn't exist")
        raise ValidationError({'message': message}, error_summary=message)
    # html_item = render_jinja2(html_item, {})
    html_item = render(html_item, {})
    extra_vars = {'title': title_item, 'html': html_item, 'page': 'hr_info'}
    return render('home/about2.html', extra_vars)


hdx_splash.add_url_rule(u'/about/license/legacy_hrinfo', view_func=about_hrinfo)
hdx_splash.add_url_rule(u'/about/<page>', view_func=about)
hdx_splash.add_url_rule(u'/', view_func=index)
