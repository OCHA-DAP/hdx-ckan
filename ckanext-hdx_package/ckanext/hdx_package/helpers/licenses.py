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
        return _("Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)")

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
        return _("Public Domain / No restrictions (CC0)")

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
    url = "https://opendatacommons.org/licenses/odbl/1-0/"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Database License (ODC-ODbL)")

class LicenseHdxOpenDataCommonsAttributionLicense(DefaultLicense):
#     domain_content = True
    id = "hdx-odc-by"
    url = "https://opendatacommons.org/licenses/by/1-0/"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Data Commons Attribution License (ODC-BY)")

class LicenseHdxOpenDataCommonsPublicdomainDedicationAndLicense(DefaultLicense):
#     domain_content = True
    id = "hdx-pddl"
    url = "https://opendatacommons.org/licenses/pddl/1-0/"
#     is_generic = True
#     is_okd_compliant = True

    @property
    def title(self):
        return _("Open Data Commons Public Domain Dedication and License (PDDL)")

class LicenseHDXCreativeCommonsAttributionInternational(DefaultLicense):
    id = "cc-by"
    od_conformance = 'approved'
    url = "http://www.opendefinition.org/licenses/cc-by"

    @property
    def title(self):
        return _("Creative Commons Attribution International (CC BY)")


class LicenseHDXCreativeCommonsAttributionShareAlike(DefaultLicense):
    # domain_content = True
    id = "cc-by-sa"
    od_conformance = 'approved'
    url = "http://www.opendefinition.org/licenses/cc-by-sa"

    @property
    def title(self):
        return _("Creative Commons Attribution Share-Alike (CC BY-SA)")
