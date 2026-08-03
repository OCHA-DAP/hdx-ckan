from flask import Blueprint

import ckan.plugins.toolkit as tk
import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_theme.views.count as count
from ckan.common import config
from ckanext.hdx_theme.helpers.caching import cached_last_three_signal_cards
import json

_ = tk._
g = tk.g
h = tk.h
check_access = tk.check_access
get_action = tk.get_action
abort = tk.abort
redirect = tk.redirect_to
render = tk.render
request = tk.request

NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError

hdx_splash = Blueprint(u'hdx_splash', __name__)


def homepage_structured_data():
    ckan_url = config.get('ckan.site_url', 'https://data.humdata.org').replace('http://', 'https://') + '/'
    search_action_url = ckan_url + 'search?q={search_term_string}'
    site_title = config.get('ckan.site_title', 'Humanitarian Data Exchange')
    site_description = config.get('ckan.site_description', '')
    logo_url = ckan_url + 'images/homepage/logo.jpg'

    organization = {
        '@type': 'Organization',
        'name': 'Humanitarian Data Exchange (HDX)',
        'url': ckan_url,
        'logo': logo_url,
        'parentOrganization': {
            '@type': 'Organization',
            'name': 'United Nations Office for the Coordination of Humanitarian Affairs (OCHA)',
            'url': 'https://www.unocha.org'
        }
    }
    if site_description:
        organization['description'] = site_description

    data = {
        '@context': 'https://schema.org',
        '@graph': [
            {
                '@type': 'WebSite',
                'url': ckan_url,
                'potentialAction': {
                    '@type': 'SearchAction',
                    'target': {
                        '@type': 'EntryPoint',
                        'urlTemplate': search_action_url
                    },
                    'query-input': 'required name=search_term_string'
                }
            },
            organization,
            {
                '@type': 'DataCatalog',
                'name': site_title,
                'url': ckan_url,
                'description': site_description,
                'provider': {
                    '@type': 'Organization',
                    'name': 'Humanitarian Data Exchange (HDX)',
                    'url': ckan_url
                }
            }
        ]
    }

    return json.dumps(data, indent=2)


def index():
    if g.userobj:
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

    datasets = json.loads(count.dataset())
    locations = json.loads(count.country())
    sources = json.loads(count.source())
    template_data = {
        'structured_data': homepage_structured_data(),
        'alert_bar': {
            'title': config.get('hdx.alert_bar_title'),
            'url': config.get('hdx.alert_bar_url'),

        },
        'count': {
            'datasets': datasets['count'],
            'locations': locations['count'],
            'sources': sources['count']
        },
        'analytics': {
            'analytics_came_from': analytics.came_from(request.args)
        },
        'signal_cards': cached_last_three_signal_cards(),
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
    title = {'hr_info': _('Legacy HR Info')}
    html = {'hr_info': 'home/snippets/hdx_hr_info.html'}

    title_item = title['hr_info']
    html_item = html['hr_info']

    if title_item is None:
        message = _("The requested about page doesn't exist")
        raise ValidationError({'message': message}, error_summary=message)
    html_item = render(html_item, {})
    extra_vars = {'title': title_item, 'html': html_item, 'page': 'hr_info'}
    return render('home/about2.html', extra_vars)


hdx_splash.add_url_rule(u'/about/license/legacy_hrinfo', view_func=about_hrinfo)
hdx_splash.add_url_rule(u'/about/<page>', view_func=about)
hdx_splash.add_url_rule(u'/', view_func=index)
