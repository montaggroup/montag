import pydb
import pydb.pyrosetup
from gluon import *


SEARCH_ITEMS_PER_PAGE = 20


def pass_paged_query_results_to_view(pdb, query, view_dict, page_number):
    items_per_page = SEARCH_ITEMS_PER_PAGE

    page_start = page_number * items_per_page
    page_end = (page_number+1) * items_per_page

    total_count, tomes = get_query_page(pdb, query, page_start, page_end)

    page_end = page_start + len(tomes)
    view_dict['page'] = page_number
    view_dict['page_start'] = page_start
    view_dict['page_end'] = page_end
    view_dict['number_results_total'] = total_count
    view_dict['tome_info'] = tomes


def build_search_query(form):
    generated_query = form.vars['query'].decode('utf-8')

    principal_language = form.vars['principal_language']
    if principal_language:
        generated_query += " principal_language:%s" % principal_language

    if 'tome_type' in form.vars:
        tome_type = form.vars['tome_type']
        if tome_type != "Z":
            generated_query += " type:%s" % tome_type
        
    return generated_query


def build_search_form(pdb):
    lang_list = pdb.get_used_languages()
    lang_dict = {lang: lang for lang in lang_list}
    lang_dict[""] = "don't care"
    form = SQLFORM.factory(
        Field('query', requires=IS_NOT_EMPTY(), default="", label="Search for"),
        Field('principal_language', default="", requires=IS_IN_SET(lang_dict)),
        Field('tome_type', label="", default="Z",
              widget=SQLFORM.widgets.radio.widget,
              requires=IS_IN_SET({
                  pydb.TomeType.Fiction: 'Fiction',
                  pydb.TomeType.NonFiction: 'Non-Fiction',
                  "Z": "Don't Care"})),
        submit_button='Search',
        _method='GET')
    return form


def get_query_page(pdb, query, start_offset, end_offset):
    index_server = pydb.pyrosetup.indexserver()
    result_tome_ids = index_server.search_tomes(query)

    tomelist = []
    for tome_id in result_tome_ids[start_offset:end_offset]:
        merge_tome = pdb.get_tome(tome_id)
        if merge_tome is not None:
            tome = pdb.get_tome_document_by_guid(merge_tome['guid'], keep_id=True,
                                                 include_local_file_info=True, include_author_detail=True)
            tomelist.append(tome)

    def tome_key(t):
        if not t['authors']:
            return ""
        return t['authors'][0]['detail']['name']
    tomelist.sort(key=tome_key)

    return len(result_tome_ids), tomelist


def pass_paged_author_query_results_to_view(pdb, query, view_dict, page_number):
    items_per_page = SEARCH_ITEMS_PER_PAGE

    page_start = page_number * items_per_page
    page_end = (page_number+1) * items_per_page

    total_count, authors = get_author_query_page(pdb, query, page_start, page_end)

    page_end = page_start+len(authors)
    view_dict['page'] = page_number
    view_dict['page_start'] = page_start
    view_dict['page_end'] = page_end
    view_dict['number_results_total'] = total_count
    view_dict['author_info'] = authors


def get_author_query_page(pdb, query, start_offset, end_offset):
    result_authors = pdb.find_authors(query) + pdb.find_authors_with_same_name_key(query)

    name_without_wildcards = query.replace('%', '').lower()

    guids = set()
    normal_authors = []
    prio_authors = []  # those will be placed in front of the result list

    for author in result_authors:
        guid = author['guid']
        if guid in guids:
            continue
        guids.add(guid)
        if author['name'].lower() == name_without_wildcards:  # prepare to place in front
            prio_authors.append(author)
        else:
            normal_authors.append(author)

    normal_authors.sort(key=lambda a: (a['name'], a['date_of_birth'], a['guid']))
    authors = prio_authors + normal_authors

    authors_slice = authors[start_offset:end_offset]
    return len(authors), authors_slice
