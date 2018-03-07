import logging

from ckan.common import config

log = logging.getLogger(__name__)


class HdxSolrReindexer(object):

    def __init__(self, context, model, package_index, query_for, text_traceback):
        super(HdxSolrReindexer, self).__init__()
        self.context = context
        self.model = model
        self.package_index = package_index
        self.query_for = query_for
        self.text_traceback = text_traceback

    def rebuild(self,
                package_id=None, only_missing=False, force=False, refresh=False,
                defer_commit=False, package_ids=None, quiet=False):
        '''
            Rebuilds the search index.

            Adapted from core ckan: lib/search/__init__.py
        '''
        log.info("Using hdx specific reindexing...")

        if package_id:

            self.package_index.remove_dict({'id': package_id})
            self._hdx_fast_reindex(self.context, [package_id], self.package_index, defer_commit, force, quiet)
        elif package_ids:
            self._hdx_fast_reindex(self.context, package_ids, self.package_index, defer_commit, False, quiet)

        else:
            package_ids = [r[0] for r in self.model.Session.query(self.model.Package.id).
                           filter(self.model.Package.state != 'deleted').all()]
            if only_missing:
                log.info('Indexing only missing packages...')
                package_query = self.query_for(self.model.Package)
                indexed_pkg_ids = set(package_query.get_all_entity_ids(
                    max_results=len(package_ids)))
                # Packages not indexed
                package_ids = set(package_ids) - indexed_pkg_ids

                if len(package_ids) == 0:
                    log.info('All datasets are already indexed')
                    return
            else:
                log.info('Rebuilding the whole index...')
                # When refreshing, the index is not previously cleared
                if not refresh:
                    self.package_index.clear()

            self._hdx_fast_reindex(self.context, package_ids, self.package_index, defer_commit, force, quiet)

    def _hdx_fast_reindex(self, context, package_ids, package_index, defer_commit, force, quiet):
        total_packages = len(package_ids)
        step = int(config.get('hdx.reindexing.batch_size', '100'))
        start = 0
        stop = step
        counter = 0
        while start < total_packages:
            import ckanext.hdx_package.helpers.reindex_helper as reindex_helper

            if not quiet:
                log.info(
                    "Indexing dataset {0}/{1}".format(
                        start, total_packages)
                )
                # sys.stdout.flush()
            try:
                pkg_dicts = reindex_helper.package_list_show_for_reindex(context, package_ids[start:stop])
                package_index.index_packages(pkg_dicts, defer_commit)
            except Exception, e:
                log.error(u'Error while indexing dataset %s: %s' %
                          (str(start), repr(e)))
                if force:
                    log.error(self.text_traceback())
                    continue
                else:
                    raise

            start = stop
            stop += step
            counter += 1