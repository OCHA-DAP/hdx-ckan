"""
Monkey patch for Datopian ckanext-sitemap extension.

This module wraps the Datopian sitemap generation function to automatically
include HDX-specific pages (events, dashboards, and potentially others).
"""

import logging
import os
from datetime import datetime

log = logging.getLogger(__name__)


def patch_sitemap_generation():
    """
    This patches the _generate_sitemap_files() function from ckanext.sitemap.sitemap
    to include HDX event and dashboard pages dynamically.
    """
    try:
        from ckanext.sitemap import sitemap as sitemap_module
        from lxml import etree
        import ckan.plugins.toolkit as tk

        # Check if already patched
        if hasattr(sitemap_module, '_hdx_sitemap_patched'):
            log.debug("HDX sitemap patch already installed, skipping")
            return

        # Save reference to original function
        original_generate_files = sitemap_module._generate_sitemap_files

        def hdx_generate_sitemap_files_wrapper():
            """
            Wrapper that generates sitemap normally, then adds HDX pages to the last file.
            """
            # Generate all sitemap files normally
            num_files = original_generate_files()

            # Post-process only the last file to add HDX pages
            last_file_index = num_files - 1
            last_file = f"sitemap-{last_file_index}.xml"
            last_file_path = os.path.join(sitemap_module.SITEMAP_DIR, last_file)

            try:
                # Read the last sitemap file
                tree = etree.parse(last_file_path)
                root = tree.getroot()

                # Add HDX pages to the XML tree
                _inject_hdx_pages(root, tk.config.get('ckan.site_url'))

                # Re-indent the entire tree to ensure consistent formatting
                etree.indent(tree, space='  ')

                # Write back with proper formatting
                tree.write(last_file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')

                log.info("HDX pages successfully injected into sitemap")

            except Exception as e:
                log.warning(f"Failed to inject HDX pages into sitemap: {str(e)}", exc_info=True)

            return num_files

        # Replace the module's function with our wrapper
        sitemap_module._generate_sitemap_files = hdx_generate_sitemap_files_wrapper

        # Mark the module as patched
        sitemap_module._hdx_sitemap_patched = True

        log.info("HDX sitemap monkey patch installed successfully")

    except ImportError as e:
        log.warning(f"ckanext-sitemap not installed, HDX sitemap patch not applied: {str(e)}")
    except Exception as e:
        log.error(f"Failed to install HDX sitemap patch: {str(e)}", exc_info=True)


def _inject_hdx_pages(urlset_root, site_url):
    """
    Helper function that adds HDX event and dashboard pages to the sitemap XML.

    :param urlset_root: The <urlset> root element from the sitemap XML
    :param site_url: Base site URL for constructing full URLs
    """
    try:
        import ckan.plugins.toolkit as tk
        from lxml import etree

        # Get XML namespace
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Get all pages using the page_list action
        context = {'ignore_auth': True}
        pages = tk.get_action('page_list')(context, {})

        # Filter for active events and dashboards
        hdx_pages = [
            page for page in pages
            if page.get('type') in ['event', 'dashboards'] and page.get('state') == 'active'
        ]

        log.debug(f"Found {len(hdx_pages)} HDX pages to add to sitemap")

        # Add each page to the sitemap
        for page in hdx_pages:
            page_name = page.get('name')
            page_type = page.get('type')

            # URL mapping: events -> /event/, dashboards -> /dashboards/
            url_type = 'dashboards' if page_type == 'dashboards' else 'event'
            page_url = f"/{url_type}/{page_name}"
            full_url = site_url + page_url

            # Parse lastmod from the page's modified timestamp
            try:
                if page.get('modified'):
                    page_lastmod = datetime.fromisoformat(page.get('modified'))
                    lastmod_str = page_lastmod.strftime('%Y-%m-%d')
                else:
                    lastmod_str = datetime.now().strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                lastmod_str = datetime.now().strftime('%Y-%m-%d')

            # Create <url> element
            url_elem = etree.SubElement(urlset_root, '{http://www.sitemaps.org/schemas/sitemap/0.9}url')

            # Add <loc> child
            loc_elem = etree.SubElement(url_elem, '{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            loc_elem.text = full_url

            # Add <lastmod> child
            lastmod_elem = etree.SubElement(url_elem, '{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            lastmod_elem.text = lastmod_str

        log.debug(f"Successfully added {len(hdx_pages)} HDX pages to sitemap")

    except Exception as e:
        # Don't let errors here break the entire sitemap generation
        log.warning(f"Error injecting HDX pages into sitemap: {str(e)}", exc_info=True)
        raise