import click
import logging

log = logging.getLogger(__name__)


@click.command(short_help='Reindexing datasets that have changed due to analytics')
def analytics_changes_reindex():
    from ckan.lib.search import rebuild

    from ckan.logic import NotFound

    length = lambda item: len(item) if item else 0

    solr_ds = _find_potential_datasets_in_solr()
    log.info('Fetched info for {} datasets from solr'.format(length(solr_ds)))

    pageviews_ds, downloads_ds = _find_potential_datasets_in_mixpanel()
    log.info('Fetched pageview info for {} datasets and download info for {} datasets from mixpanel'
                  .format(length(pageviews_ds), length(downloads_ds)))

    ds_to_update = _decide_which_datasets_need_update(solr_ds, pageviews_ds, downloads_ds)

    total = len(ds_to_update)
    log.info('Rebuilding index for {} datasets.'.format(total))

    for idx, dataset_id in enumerate(ds_to_update):
        log.info('Rebuilding index for dataset {}. {}/{}'.format(dataset_id, idx + 1, total))
        try:
            rebuild(dataset_id)
            log.info('Done')
        except NotFound:
            log.error("Error: package {} not found.".format(dataset_id))
        except KeyboardInterrupt:
            log.error("Stopped.")
            return
        except:
            raise


def _find_potential_datasets_in_solr():
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
    except Exception as e:
        log.warn('Error in searching solr {}'.format(str(e)))

    return dataseta_meta_map


def _find_potential_datasets_in_mixpanel():
    from ckanext.hdx_theme.util.jql import downloads_per_dataset_all_cached, \
        pageviews_per_dataset_last_14_days_cached

    dataset_2_downloads_map = downloads_per_dataset_all_cached()
    dataset_2_pageviews_map = pageviews_per_dataset_last_14_days_cached()

    return dataset_2_pageviews_map, dataset_2_downloads_map


def _decide_which_datasets_need_update( solr_ds, pageviews_ds, downloads_ds):
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
