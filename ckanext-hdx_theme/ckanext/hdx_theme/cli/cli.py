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

    def _find_potential_datasets_in_solr(self):
        from ckan.lib.search.query import make_connection
        dataseta_meta_map = {}
        data_dict = {
            'q': '*:*',
            'fl': 'id pageviews_last_14_days total_res_downloads',
            'fq': 'total_res_downloads:[1 TO *] OR pageviews_last_14_days: [1 TO *]',
            'start': 0,
            'rows': 1000000
        }
        try:
            conn = make_connection(decode_dates=False)
            search_result = conn.search(**data_dict)
            dataseta_meta_map = {d['id']: {'pageviews': d.get('pageviews_last_14_days', 0),
                                           'downloads': d.get('total_res_downloads', 0)}
                                 for d in search_result.docs}
        except Exception, e:
            self.log.warn('Error in searching solr {}'.format(str(e)))

        return dataseta_meta_map

    def _find_potential_datasets_in_mixpanel(self):
        from ckanext.hdx_theme.util.jql import downloads_per_dataset_all_cached, \
            pageviews_per_dataset_last_14_days_cached
        from ckan.common import config

        dataset_2_downloads_map = downloads_per_dataset_all_cached()
        dataset_2_pageviews_map = pageviews_per_dataset_last_14_days_cached()

        return dataset_2_pageviews_map, dataset_2_downloads_map

    def _decide_which_datasets_need_update(self, solr_ds, pageviews_ds, downloads_ds):
        '''
        :param solr_ds:
        :type solr_ds: dict
        :param pageviews_ds:
        :type pageviews_ds: dict
        :param downloads_ds:
        :type downloads_ds: dict
        :return:
        '''
        ds_to_update = []

        for id, meta_data in solr_ds.items():
            pv_value = pageviews_ds.get(id, 0)
            dw_value = downloads_ds.get(id, 0)

            if pv_value != meta_data.get('pageviews') or dw_value != meta_data.get('downloads'):
                ds_to_update.append(id)

        for id in pageviews_ds:
            if id and id not in solr_ds:
                ds_to_update.append(id)

        for id in downloads_ds:
            if id and id not in solr_ds:
                ds_to_update.append(id)

        return ds_to_update


    def command(self):

        from ckan.lib.search import rebuild

        from ckan.logic import NotFound

        self._load_config()
        # hours_to_check = int(config.get('hdx.analytics.hours_to_check_for_refresh', 24))

        self.log = logging.getLogger(__name__)

        solr_ds = self._find_potential_datasets_in_solr()
        pageviews_ds, downloads_ds = self._find_potential_datasets_in_mixpanel()

        ds_to_update = self._decide_which_datasets_need_update(solr_ds, pageviews_ds, downloads_ds)

        total = len(ds_to_update)
        self.log.info('Rebuilding index for {} datasets.'.format(total))

        for idx, dataset_id in enumerate(ds_to_update):
            self.log.info('Rebuilding index for dataset {}. {}/{}'.format(dataset_id, idx+1, total))
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
