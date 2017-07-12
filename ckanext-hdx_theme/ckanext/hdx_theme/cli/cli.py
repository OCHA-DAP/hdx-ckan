import ckan.lib.cli as cli
import logging as logging

class CustomLessCompile(cli.CkanCommand):
    summary = 'Compile all custom less themes'

    def command(self):
        self._load_config()

        import ckan.model as model
        import ckanext.hdx_org_group.helpers.organization_helper as org_helper

        self.log = logging.getLogger(__name__)
        self.log.info("Recompiling all custom less themes")

        org_helper.recompile_everything({'model': model, 'session': model.Session,
                                         'user': 'hdx', 'ignore_auth': True})

        self.log.info("Done")


class AnalyticsChangesReindex(cli.CkanCommand):
    summary = 'Reindexing datasets that have changed due to analytics'

    def command(self):
        from ckanext.hdx_theme.util.jql import downloads_per_dataset
        from ckan.lib.search import rebuild
        from ckan.common import config
        from ckan.logic import NotFound

        hours_to_check = int(config.get('hdx.analytics.hours_to_check_for_refresh', 24))

        self._load_config()

        self.log = logging.getLogger(__name__)

        dataset_2_downloads_map = downloads_per_dataset(hours_to_check)

        for dataset_id in dataset_2_downloads_map.keys():
            self.log.info('Rebuilding index for dataset {}'.format(dataset_id))
            try:
                rebuild(dataset_id)
                self.log.info('Done')
            except NotFound:
                self.log.error("Error: package {} not found.".format(dataset_id))
            except KeyboardInterrupt:
                self.log.error("Stopped.")
                return
            except:
                raise
