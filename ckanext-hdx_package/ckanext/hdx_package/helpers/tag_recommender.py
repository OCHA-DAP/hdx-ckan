
import logging

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

get_action = tk.get_action


class TagRecommender(object):

    FACET_LIMIT = 10

    def __init__(self, title, organization, extra_fq=None, with_retry=True, facet_limit=FACET_LIMIT):
        super(TagRecommender, self).__init__()
        self.title = title
        self.organization = organization
        self.extra_fq = extra_fq
        self.with_retry = with_retry
        self.facet_limit = facet_limit

    def find_recommended_tags(self):
        if self.title:
            q = self.title
            if self.organization:
                q += ' "{}"'.format(self.organization)
            q = q.replace(':', ' ')
            data_dict = {
                'rows': 1,
                'facet': 'on',
                'facet.field': ['vocab_Topics'],
                'facet.limit': self.facet_limit,
                'qf': 'name^4 title^4 organization^2 groups^2 text',
                'mm': '2<-1 5<60%',
                'q': q
            }
            if self.extra_fq:
                data_dict['fq'] = self.extra_fq

            result = get_action('package_search')({}, data_dict)

            try:
                facet_dict = result['facets']['vocab_Topics']
                facet_list = sorted(
                    ({'name':k, 'count':v} for k, v in facet_dict.items()),
                    key=lambda facet_tuple: facet_tuple['count'],
                    reverse=True
                )
                if len(facet_list) <= 2 and self.organization and self.with_retry:
                    log.info(u'Retrying for {}'.format(q))
                    self.organization = None
                    return self.find_recommended_tags()
                # log.info('Recommened tags: ' + str(facet_list))
                return facet_list
            except KeyError as e:
                log.warn('No vocab_Topics facets found')

        return []


class TagRecommenderTest(object):
    LIMIT = 100

    def __init__(self, limit=LIMIT, page=1, just_percentage='false', with_retry='true', all='false',
                 facet_limit=TagRecommender.FACET_LIMIT, dataset_name=None):
        super(TagRecommenderTest, self).__init__()
        self.limit = int(limit)
        self.page = int(page)
        self.just_percentage = just_percentage == 'true'
        self.with_retry = with_retry == 'true'
        self.all = all == 'true'
        self.facet_limit = int(facet_limit)
        self.dataset_name = dataset_name

        if self.all:
            self.limit = self.LIMIT
            self.just_percentage = True

    def find_packages(self, page):
        data_dict = {
            'rows': self.limit,
            'start': (page - 1) * self.limit,
            'q': ''
        }
        if self.dataset_name:
            data_dict['fq'] = 'name:{}'.format(self.dataset_name)

        result = get_action('package_search')({}, data_dict)
        simple_result = [{
            'title': ds_dict['title'],
            'name': ds_dict['name'],
            'organization': ds_dict['organization']['name'],
            'tags': [tag['name'] for tag in ds_dict.get('tags', []) if tag.get('vocabulary_id')]
        } for ds_dict in result.get('results', [])]
        return simple_result, result['count']

    def run_test(self):
        percentages_per_dataset = []
        more_pages_exist = True
        datasets = []
        while more_pages_exist:
            datasets, total = self.find_packages(self.page)
            more_pages_exist = (self.page * self.limit < total) and self.all

            log.info('Page {} out of {}'.format(self.page, (total/self.limit)+1))
            for dataset in datasets:
                fq = 'type:dataset -name:{}'.format(dataset['name'])
                recommended_tags = TagRecommender(dataset['title'], dataset['organization'],
                                                  extra_fq=fq, with_retry=self.with_retry,
                                                  facet_limit=self.facet_limit).find_recommended_tags()
                dataset['recommended_tags'] = [tag.get('name') for tag in recommended_tags]

                tags_found = 0
                if dataset['tags']:
                    for tag in dataset['tags']:
                        if tag in dataset['recommended_tags']:
                            tags_found += 1
                    dataset['percentage_found'] = 100*tags_found / len(dataset['tags'])
                    percentages_per_dataset.append(dataset['percentage_found'])
            self.page += 1

        percentage_found = sum(percentages_per_dataset) / len(percentages_per_dataset) if percentages_per_dataset else 0

        results = {'pecentage_found': percentage_found}

        if not self.just_percentage:
            results['datasets'] = datasets
        return results

