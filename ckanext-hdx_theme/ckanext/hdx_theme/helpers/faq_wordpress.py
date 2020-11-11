import logging
import pylons.config as config
import requests

log = logging.getLogger(__name__)

def get_headers():
    wp_auth_basic = config.get('hdx.wordpress.auth.basic')

    headers = {}
    if wp_auth_basic:
        headers['Authorization'] = 'Basic {0}'.format(wp_auth_basic)

    return headers

def get_faq_data(category):
    wp_url = config.get('hdx.wordpress.url')
    headers = get_headers()
    response = requests.get('{0}/wp-json/wp/v2/ufaq-category?parent={1}'.format(wp_url, category),
                            headers=headers)
    json = response.json()
    log.error(json)
    map = {}
    for category in json:
        map[category['id']] = {
            'title': category['name'],
            'questions': []
        }
    id_csv = ','.join(str(v) for v in map.keys())
    response = requests.get('{0}/wp-json/wp/v2/ufaq?ufaq-category={1}'.format(wp_url, id_csv),
                            headers = headers)
    json = response.json()
    for item in json:
        for categ_id in item['ufaq-category']:
            map[categ_id]['questions'].append({
                'q': item['title']['rendered'],
                'a': item['content']['rendered']
            })
    response = []
    for categ_id in map:
        response.append(map[categ_id])

    return response

def get_post(id):
    response = requests.get('{0}/wp-json/wp/v2/ufaq/{1}'.format(config.get('hdx.wordpress.url'), id),
                            headers = get_headers())
    json = response.json()
    return json['content']['rendered']

def faq_for_category(category):
    data = get_faq_data(category)
    for section in data:
        s_id = ''.join(i if i.isalnum() else '_' for i in section['title'])
        s_id = 'faq-{}'.format(s_id)
        section['id'] = s_id
        for question in section['questions']:
            try:
                q_id = ''.join(i if i.isalnum() else '_' for i in question['q'])
                question['id'] = q_id
            except Exception, ex:
                log.error(ex)

    topics = {}
    for f in data:
        topics[f.get('id')] = f.get('title')

    return {
        'faq_data': data,
        'topics': topics
    }
