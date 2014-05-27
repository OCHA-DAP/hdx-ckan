import sys, re
import ckan.lib.base as base
from ckan.lib.base import request
from ckan.lib.base import c,g,h
from ckan.lib.base import model
from ckan.lib.base import render
from ckan.lib.base import _
import ckan.logic as logic
import ckan.plugins.toolkit as tk

from ckan.controllers.group import GroupController as gc
from ckan.controllers.home import HomeController

from ckanext.hdx_theme.country_list_hardcoded import FOCUS_COUNTRIES

from beaker.cache import cache_regions, cache_region

NotAuthorized = logic.NotAuthorized
check_access = logic.check_access
get_action = logic.get_action

def filter_focus_countries(group_package_stuff):
	focus_group_package_stuff = []
	for grp_dict in group_package_stuff:
		if grp_dict['display_name'] in FOCUS_COUNTRIES:
			focus_group_package_stuff.append(grp_dict)
				
	return focus_group_package_stuff

# Cache region is defined in plugin.py in metadata plugin
@cache_region('hdx_memory_cache', 'focus_countries_list')
def cached_get_group_package_stuff():
	group_package_stuff = tk.get_action('group_list')(data_dict={'all_fields': True})
	focus_group_package_stuff = filter_focus_countries(group_package_stuff)
	
	return sorted(focus_group_package_stuff, key=lambda k: k['title'])
	
cached_get_group_package_stuff()  

class SplashPageController(HomeController):

	group_type = 'group'

	def index(self):
		group_type = None
		context = {'model': model, 'session': model.Session,
				   'user': c.user or c.author, 'for_view': True,
				   'with_private': False}

		q = c.q = request.params.get('q', '')
		data_dict = {'all_fields': True, 'q': q}
		sort_by = c.sort_by_selected = request.params.get('sort')
		if sort_by:
			data_dict['sort'] = sort_by
		try:
			self._check_access('site_read', context)
		except NotAuthorized:
			abort(401, _('Not authorized to see this page'))
		if c.userobj:
			context['user_id'] = c.userobj.id
			context['user_is_admin'] = c.userobj.sysadmin
		
		
		
		c.group_package_stuff = cached_get_group_package_stuff()

		##Removing groups without geojson for the map
		c.group_map = []
		for gp in c.group_package_stuff:
			for e in gp['extras']:
				if e['key'] == 'geojson' and e['value']:
					c.group_map.append(gp)

		#print c.group_package_stuff

		if c.userobj is not None:
			msg = None
			url = h.url_for(controller='user', action='edit')
			is_google_id = \
				c.userobj.name.startswith('https://www.google.com/accounts/o8/id')
			if not c.userobj.email and (is_google_id and not c.userobj.fullname):
				msg = _(u'Please <a href="{link}">update your profile</a>'
						u' and add your email address and your full name. '
						u'{site} uses your email address'
						u' if you need to reset your password.'.format(
							link=url, site=g.site_title))
			elif not c.userobj.email:
				msg = _('Please <a href="%s">update your profile</a>'
						' and add your email address. ') % url + \
					_('%s uses your email address'
						' if you need to reset your password.') \
					% g.site_title
			elif is_google_id and not c.userobj.fullname:
				msg = _('Please <a href="%s">update your profile</a>'
						' and add your full name.') % (url)
			if msg:
				h.flash_notice(msg, allow_html=True)

		return base.render('home/index.html', cache_force=True)

	def _check_access(self, action_name, *args, **kw):
		''' select the correct group/org check_access '''
		return check_access(self._replace_group_org(action_name), *args, **kw)

	def _replace_group_org(self, string):
		''' substitute organization for group if this is an org'''
		if self.group_type == 'organization':
			string = re.sub('^group', 'organization', string)
		return string

	def _action(self, action_name):
		''' select the correct group/org action '''
		return get_action(self._replace_group_org(action_name))
	
