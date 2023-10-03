from pyalex import Works, Authors, Sources, Institutions, Concepts, Publishers, Funders
from pyalex.api import QueryError
from requests import HTTPError

from .cache import get_openalex_entities_cache, set_openalex_entities_cache, get_openalex_single_entity_cache, \
    set_openalex_single_entity_cache

entities = {
    'work': Works,
    'author': Authors,
    'source': Sources,
    'institution': Institutions,
    'concept': Concepts,
    'publisher': Publishers,
    'funder': Funders
}

entities_fields = {
    'work': ['id', 'display_name', 'publication_year',
             'publication_date', 'language', 'type',
             'abstract_inverted_index', 'authorships',
             'concepts', 'cited_by_count'],
    'author': ['id', 'display_name', 'works_count',
               'cited_by_count', 'x_concepts',
               'last_known_institution'],
    'source': ['id', 'display_name', 'country_code', 'type'],
    'institution': ['id', 'display_name', 'country_code', 'type',
                    'image_url', 'international', 'x_concepts'],
    'concept': ['id', 'display_name', 'international'],
    'publisher': ['id', 'display_name', 'alternate_titles',
                  'country_codes', 'image_url'],
    'funder': ['id', 'display_name', 'alternate_titles',
               'country_code', 'description', 'image_url']
}


def search_entities(type: str, search: str, position: str = 'default', filter: dict = None, sort: dict = None,
                    page: int = 1, size: int = 25):
    if not position:
        position = 'default'
    if not filter:
        filter = {}
    if not sort:
        sort = {}
    result = get_openalex_entities_cache(type, search, position, filter, sort, page, size)
    if result is None:
        try:
            result, meta = entities[type]().search_filter(**{position: search}) \
                .filter(**filter).sort(**sort).select(entities_fields[type]) \
                .get(return_meta=True, page=page, per_page=size)
        except QueryError as e:
            return e.args[0], False
        except HTTPError as e:
            if e.response.status_code == 404:
                return '不存在对应id的实体', False
            print(e.args)
            return 'OpenAlex请求出错', False
        except Exception as e:
            print(e.args)
            return '未知错误', False
        if type == 'work':
            for r in result:
                r['abstract'] = r['abstract']
                del r['abstract_inverted_index']
        result = {
            'total': meta['count'],
            'page': meta['page'],
            'size': meta['per_page'],
            'result': result
        }
        set_openalex_entities_cache(result, type, search, position, filter, sort, page, size)
    return result, True


def search_entities_by_body(type: str, data: dict):
    """
    根据请求体参数搜索entities
    :param type: entities类别
    :param data: 转为字典的请求体
    :return:
    """
    search = data.get('search', '')
    position = data.get('position', 'default')
    filter = data.get('filter', {})
    sort = data.get('sort', {})
    page = int(data.get('page', 1))
    size = int(data.get('size', 25))

    temp = filter.copy()
    for key, value in temp.items():
        if not value:
            filter.pop(key)
        if isinstance(value, list):
            filter[key] = '|'.join(value)
    temp = sort.copy()
    for key, value in temp.items():
        if not value:
            sort.pop(key)
    result = search_entities(type, search, position, filter, sort, page, size)
    return result


def search_works_by_author_id(id: str):
    try:
        result = Works().filter(author={"id": id}) \
            .select(entities_fields['work']).get()
        for r in result:
            r['abstract'] = r['abstract']
            del r['abstract_inverted_index']
    except:
        return None
    return result


def calculate_collaborators(works: list, id: str):
    """
    根据指定作者的所有论文计算所有合作者信息
    :param works: 作者的所有论文
    :param id: 作者的id
    :return: 作者的所有合作者
    """
    collaborators = {}
    for work in works:
        for author in work['authorships']:
            author = author['author']
            if author['id'] == id:
                continue
            if author['id'] not in collaborators.keys():
                author['cooperation_times'] = 0
                author['collaborative_works'] = []
                collaborators[author['id']] = author
            collaborators[author['id']]['cooperation_times'] += 1
            collaborators[author['id']]['collaborative_works'].append({
                'id': work['id'],
                'display_name': work['display_name']
            })
    collaborators = sorted(collaborators.values(),
                           key=lambda x: x['cooperation_times'],
                           reverse=True)
    return collaborators


def get_single_entity(type: str, id: str):
    result = get_openalex_single_entity_cache(type, id)
    if result is None:
        try:
            result = entities[type]()[id]
        except QueryError as e:
            return e.args[0], False
        except HTTPError as e:
            if e.response.status_code == 404:
                return '不存在对应id的实体', False
            print(e.args)
            return 'OpenAlex请求出错', False
        except Exception as e:
            print(e.args)
            return '未知错误', False
        if type == 'work':
            result['abstract'] = result['abstract']
            del result['abstract_inverted_index']

            result['referenced_works'] = Works(
                {'select': ['id', 'display_name', 'publication_year']}
            )[result['referenced_works'][0:20]]
            result['related_works'] = Works(
                {'select': ['id', 'display_name', 'publication_year']}
            )[result['related_works'][0:20]]

        if type == 'author':
            result['works'] = search_works_by_author_id(id)
            result['collaborators'] = calculate_collaborators(result['works'], id)

        set_openalex_single_entity_cache(result, type, id)

    return result, True
