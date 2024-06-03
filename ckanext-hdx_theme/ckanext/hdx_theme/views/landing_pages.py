import logging
import flask
import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.faq_wordpress as fw
from ckan.common import config
from ckanext.hdx_theme.helpers.ui_constants.landing_pages.hapi import \
    DATA_COVERAGE_CONSTANTS as HAPI_DATA_COVERAGE_CONSTANTS, SECTIONS_CONSTANTS as HAPI_SECTIONS_CONSTANTS
from ckanext.hdx_theme.helpers.ui_constants.landing_pages.signals import \
    DATA_COVERAGE_CONSTANTS as SIGNALS_DATA_COVERAGE_CONSTANTS, SECTIONS_CONSTANTS as SIGNALS_SECTIONS_CONSTANTS

abort = tk.abort
g = tk.g
check_access = tk.check_access
get_action = tk.get_action
render = tk.render

log = logging.getLogger(__name__)

hdx_landing_pages = flask.Blueprint(u'hdx_landing_pages', __name__, url_prefix=u'/')


def hapi():
    wp_category_terms = config.get('hdx.wordpress.category.hapi')
    data = fw.faq_for_category(wp_category_terms)

    partners = [
        ('european_comission', 'European Commission'),
        ('acled', 'ACLED'),
        ('inform', 'INFORM'),
        ('ipc', 'IPC'),
        ('unfpa', 'UNFPA'),
        ('ophi', 'OPHI'),
        ('unchr', 'UNHCR'),
        ('ocha', 'OCHA'),
        ('wfp', 'WFP')
    ]
    sections = HAPI_SECTIONS_CONSTANTS
    data_coverage = HAPI_DATA_COVERAGE_CONSTANTS

    template_data = {
        'partners': partners,
        'sections': sections,
        'data_coverage': data_coverage,
        'faq_data': data['faq_data'],
    }

    return render('landing_pages/hapi.html', extra_vars=template_data)


def signals():
    wp_category_terms = config.get('hdx.wordpress.category.signals')
    data = fw.faq_for_category(wp_category_terms)

    partners = [
        ('european_comission', 'European Commission'),
        ('acled', 'ACLED'),
        ('ipc', 'IPC'),
        ('idmc', 'IDMC'),
        ('wfp', 'WFP')
    ]

    sections = SIGNALS_SECTIONS_CONSTANTS
    data_coverage = SIGNALS_DATA_COVERAGE_CONSTANTS

    template_data = {
        'partners': partners,
        'sections': sections,
        'data_coverage': data_coverage,
        'faq_data': data['faq_data'],
    }

    return render('landing_pages/signals.html', extra_vars=template_data)


# hdx_landing_pages.add_url_rule(u'/hapi/', view_func=hapi, strict_slashes=False)
# hdx_landing_pages.add_url_rule(u'/signals/', view_func=signals, strict_slashes=False)
