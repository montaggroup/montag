def _pass_paged_query_results_to_view(query, view_dict, page_number):
    items_per_page = 20

    page_start = page_number * items_per_page
    page_end = (page_number+1) * items_per_page

    total_count, tomes  = _get_query_page(query, page_start, page_end)

    page_end=page_start+len(tomes)
    view_dict['page'] = page_number
    view_dict['page_start'] = page_start
    view_dict['page_end'] = page_end
    view_dict['number_results_total'] = total_count
    view_dict['tome_info'] = tomes

def _build_search_query(form):
    generated_query = form.vars['query'].decode('utf-8')

    principal_language = form.vars['principal_language']
    if principal_language:
        generated_query += " principal_language:%s" % principal_language

    if 'tome_type' in form.vars:
        tome_type = form.vars['tome_type']
        if tome_type != "Z":
            generated_query += " type:%s" % tome_type
        
    return generated_query


def _build_search_form():
    lang_list = get_used_languages()
    lang_dict = {lang: lang for lang in lang_list}
    lang_dict[""] = "don't care"
    form = SQLFORM.factory(
        Field('query',requires=IS_NOT_EMPTY(), default="", label="Search for"),
        Field('principal_language', default="", requires=IS_IN_SET(lang_dict)),
        Field('tome_type', label="", default="Z" , widget=SQLFORM.widgets.radio.widget, requires=IS_IN_SET({TomeType.Fiction:'Fiction',TomeType.NonFiction:'Non-Fiction', "Z": "Don't Care"})),
        submit_button='Search',
        _method = 'GET')
    return form



def _get_query_page(query, start_offset, end_offset):
    index_server = pydb.pyrosetup.indexserver()
    result_tome_ids = index_server.search_tomes(query)

    tomelist=[]
    for tome_id in result_tome_ids[start_offset:end_offset]:
        merge_tome = db.get_tome(tome_id)
        if merge_tome is not None:
            tome = db.get_tome_document_with_local_overlay_by_guid(merge_tome['guid'], include_local_file_info=True, include_author_detail=True)
            tomelist.append(tome)

    def tome_key(t):
        if not t['authors']:
            return ""
        return t['authors'][0]['detail']['name']
    tomelist.sort(key=tome_key)

    return len(result_tome_ids), tomelist


def _get_author_query_page(query, start_offset, end_offset):
    result_authors = db.find_authors(query)

    authorlist=result_authors[start_offset:end_offset]
    return len(result_authors), authorlist


def _pass_paged_author_query_results_to_view(query, view_dict, page_number):
    items_per_page = 20

    page_start = page_number * items_per_page
    page_end = (page_number+1) * items_per_page

    total_count, authors  = _get_author_query_page(query, page_start, page_end)

    page_end=page_start+len(authors)
    view_dict['page'] = page_number
    view_dict['page_start'] = page_start
    view_dict['page_end'] = page_end
    view_dict['number_results_total'] = total_count
    view_dict['author_info'] = authors
