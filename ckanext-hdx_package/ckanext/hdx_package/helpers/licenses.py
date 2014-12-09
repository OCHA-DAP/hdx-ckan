'''
Created on May 12, 2014

@author: alexandru-m-g
'''

from ckan.common import _
from ckan.model.license import DefaultLicense


class LicenseCreativeCommonsIntergovernmentalOrgs(DefaultLicense):
#     domain_content = True
#     domain_data = True
    id = "cc-by-igo"
    is_okd_compliant = False
    url = "http://creativecommons.org/licenses/by/3.0/igo/legalcode"

    @property
    def title(self):
        return _("Creative Commons Attribution for Intergovernmental Organisations")
    
#class LicenseCreativeCommonsNoDerives(DefaultLicense):
#     domain_content = True
#     domain_data = True
#    id = "cc-by-nd"
#    is_okd_compliant = False
#    url = "http://creativecommons.org/licenses/by-nd/3.0/legalcode"

#    @property
#    def title(self):
#        return _("Creative Commons Attribution-NoDerives")
    
class LicenseOtherPublicDomainNoRestrictions(DefaultLicense):
#     domain_content = True
    id = "other-pd-nr"
    is_generic = True
    is_okd_compliant = True

    @property
    def title(self):
        return _("Public Domain / No Restrictions")

class LicenseHdxMultiple(DefaultLicense):
#     domain_content = True
    id = "hdx-multi"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Multiple Licenses")

class LicenseHdxOther(DefaultLicense):
#     domain_content = True
    id = "hdx-other"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Other")


class LicenseHdxOpenDatabaseLicense(DefaultLicense):
#     domain_content = True
    id = "hdx-odc-odbl"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Database License (ODC-ODbL)")

class LicenseHdxOpenDataCommonsAttributionLicense(DefaultLicense):
#     domain_content = True
    id = "hdx-odc-by"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Data Commons Attribution License (ODC-BY)")

class LicenseHdxOpenDataCommonsPublicdomainDedicationAndLicense(DefaultLicense):
#     domain_content = True
    id = "hdx-pddl"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Data Commons Public Domain Dedication and License (PDDL)")
