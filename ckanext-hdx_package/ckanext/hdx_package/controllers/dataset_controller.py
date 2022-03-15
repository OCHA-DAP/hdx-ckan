"""
Functions for creating and maintaining datasets.
"""
# import logging
#
# import ckan.lib.base as base
# import ckan.lib.helpers as h
# import ckan.lib.navl.dictization_functions as dict_fns
# import ckan.lib.plugins
# import ckan.logic as logic
# from ckan.common import _, json, request, c, response
# from ckan.controllers.package import PackageController
# from ckan.lib.mailer import MailerException
# from ckanext.hdx_theme.util.mail import hdx_validate_email
#
# log = logging.getLogger(__name__)
#
# render = base.render
# abort = base.abort
# redirect = h.redirect_to
#
# NotFound = logic.NotFound
# NotAuthorized = logic.NotAuthorized
# ValidationError = logic.ValidationError
# check_access = logic.check_access
# get_action = logic.get_action
# tuplize_dict = logic.tuplize_dict
# clean_dict = logic.clean_dict
# parse_params = logic.parse_params
# flatten_to_string_key = logic.flatten_to_string_key
# DataError = ckan.lib.navl.dictization_functions.DataError
# _check_group_auth = logic.auth.create._check_group_auth

# SUCCESS = json.dumps({'success': True})
#
# lookup_package_plugin = ckan.lib.plugins.lookup_package_plugin


# class DatasetController(PackageController):


    # def _create_perma_link_if_needed(self, dataset_id, resource):
    #     """
    #     Create a perma link
    #     """
    #     if 'perma_link' not in resource and resource.get('resource_type', '') == 'file.upload':
    #         domain = config.get('ckan.site_url', '')
    #         if domain and domain in resource.get('url', ''):
    #             perma_link = h.url_for(
    #                 'perma_storage_file', id=dataset_id, resource_id=resource['id'])
    #             resource['perma_link'] = domain + perma_link


    # def _has_views(self, resources):
    #     view_enabled_resources = (r for r in resources if r.get('no_preview') != 'true')
    #     for resource in view_enabled_resources:
    #         if self._has_shape_info(resource):
    #             return {'type': 'hdx_geo_preview', 'default': None}
    #         _default_view = self._has_hxl_views(resource)
    #         if _default_view:
    #             _default_view['type'] = 'hdx_hxl_preview'
    #             return _default_view
    #     return None


    # @staticmethod
    # def _get_json_from_resource(resource):
    #     """
    #     Get json from the resource files
    #     """
    #     if not resource:
    #         return None
    #     urls_dict = {'url': resource}
    #     g_json = get_action('hdx_get_json_from_resource')({}, urls_dict)
    #     return g_json
    #
    # @staticmethod
    # def _get_geojson(url):
    #     """
    #     Get geojson from resources
    #     """
    #     ogre_url = config.get('hdx.ogre.url')
    #     urls_dict = {'shape_source_url': url, 'convert_url': ogre_url+'/convert'}
    #     g_json = get_action('hdx_get_shape_geojson')({}, urls_dict)
    #     return g_json
    #
    # def _get_shape_info_as_json(self, gis_data):
    #     resource_id = gis_data['resource_id']
    #     resource_id = resource_id if resource_id and resource_id.strip() else 'new'
    #
    #     layer_import_url = config.get('hdx.gis.layer_import_url')
    #     gis_url = layer_import_url.replace("{dataset_id}", gis_data['dataset_id']).replace("{resource_id}",
    #                 resource_id).replace("{resource_download_url}", gis_data['url'])
    #     result = get_action('hdx_get_shape_info')({}, {"gis_url": gis_url})
    #     return result

    # copy from package.py:1094
    # def resource_delete(self, id, resource_id):
    #     """
    #     Delete a resource, HDX changed the redirection point.
    #     """
    #
    #     if 'cancel' in request.params:
    #         h.redirect_to(
    #             controller='package', action='resource_edit', resource_id=resource_id, id=id)
    #
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author, 'auth_user_obj': c.userobj}
    #
    #     try:
    #         check_access('package_delete', context, {'id': id})
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to delete package %s') % '')
    #
    #     try:
    #         if request.method == 'POST':
    #             get_action('resource_delete')(context, {'id': resource_id})
    #             h.flash_notice(_('Resource has been deleted.'))
    #             h.redirect_to(controller='package', action='resources',
    #                           id=id)
    #         c.resource_dict = get_action('resource_show')(
    #             context, {'id': resource_id})
    #         c.pkg_id = id
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to delete resource %s') % '')
    #     except NotFound:
    #         abort(404, _('Resource not found'))
    #     return render('package/confirm_delete_resource.html', {'dataset_type': self._get_package_type(id)})

    # def resource_download(self, id, resource_id):
    #     '''
    #     This is a wrapper of the core ckan function.
    #     It's meant to allow old style HDX perma_links (/dataset/{id}/resource_download/{resource_id})
    #     to still function for ppl that have bookmarked the url or for custom pages.
    #
    #     :param id: package id
    #     :type id: string
    #     :param resource_id: resource id
    #     :type resource_id: string
    #     :return:
    #     :rtype:
    #     '''
    #     result = super(DatasetController, self).resource_download(id, resource_id)
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author, 'auth_user_obj': c.userobj}
    #
    #     try:
    #         rsc = get_action('resource_show')(context, {'id': resource_id})
    #         response.headers['Content-Disposition'] = 'inline; filename="{}"'.format(rsc.get('name', 'download'))
    #     except NotFound:
    #         abort(404, _('Resource not found'))
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to read resource %s') % id)
    #
    #     return result

    # def resource_datapreview(self, id, resource_id):
    #     '''
    #     Modified by HDX - from package controller.
    #     - change to have protocol-relative URL
    #
    #     Embeded page for a resource data-preview.
    #
    #     Depending on the type, different previews are loaded.  This could be an
    #     img tag where the image is loaded directly or an iframe that embeds a
    #     webpage, recline or a pdf preview.
    #     '''
    #     context = {
    #         'model': model,
    #         'session': model.Session,
    #         'user': c.user or c.author,
    #         'auth_user_obj': c.userobj
    #     }
    #
    #     try:
    #         c.resource = get_action('resource_show')(context,
    #                                                  {'id': resource_id})
    #         c.package = get_action('package_show')(context, {'id': id})
    #
    #         data_dict = {'resource': c.resource, 'package': c.package}
    #
    #         preview_plugin = datapreview.get_preview_plugin(data_dict)
    #
    #         if preview_plugin is None:
    #             abort(409, _('No preview has been defined.'))
    #
    #         preview_plugin.setup_template_variables(context, data_dict)
    #
    #         # If the browser is going to make a direct request (not via dataproxy) for
    #         # the resource it needs to have protocol-relative url
    #         if preview_plugin and preview_plugin.name == 'text_preview':
    #             c.resource['url'] = c.resource['url'].replace('http://', '//').replace(':5000', '')
    #
    #         c.resource_json = json.dumps(c.resource)
    #     except NotFound:
    #         abort(404, _('Resource not found'))
    #     except NotAuthorized:
    #         abort(403, _('Unauthorized to read resource %s') % id)
    #     else:
    #         return render(preview_plugin.preview_template(context, data_dict))
