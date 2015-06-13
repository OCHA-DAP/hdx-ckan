import ckan.lib.cli as cli


class CustomLessCompile(cli.CkanCommand):
    summary = 'Compile all custom less themes'
    def command(self):
        self._load_config()
        import logging as logging
        import ckan.model as model
        import ckanext.hdx_org_group.helpers.organization_helper as org_helper

        self.log = logging.getLogger(__name__)
        self.log.info("Recompiling all custom less themes")

        org_helper.recompile_everything({'model': model, 'session': model.Session,
                   'user': 'hdx', 'ignore_auth': True})

        self.log.info("Done")
