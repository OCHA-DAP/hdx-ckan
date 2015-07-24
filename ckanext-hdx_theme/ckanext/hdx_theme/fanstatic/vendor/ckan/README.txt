Since in the ckan/public/base/javascript/resource.config file we have a dependency "ckan = vendor/bootstrap", we can't
load any of the ckan dependencies separately.
Solution to still use Bootstrap 3.2 and not to modify the CKAN core implies that we need to copy the core scripts that
we rely on in this folder and add them in the fanstatic resource "hdx_theme/ckan" :)

