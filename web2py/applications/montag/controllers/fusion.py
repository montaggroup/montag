# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *

from pydb_helpers.pydb_functions import db_str_to_form, read_form_field
from pydb_helpers import search_forms
from pydb import network_params


def _select_author_merge_partner_form(first_author):
    form = SQLFORM.factory(Field('query', requires=IS_NOT_EMPTY(), default=db_str_to_form(first_author['name']),
                                 label="Search for"),
                           submit_button='Search',
                           _method='GET')
    return form


@auth.requires_login()
def select_author_merge_partner():
    first_author_guid = request.args[0]
    first_author = pdb.get_author_by_guid(first_author_guid)
    
    if first_author is None:
        session.flash = "Author not found"
        redirect(URL('default', 'tomesearch'))
        return 

    search_form = _select_author_merge_partner_form(first_author)
    
    retval = {'first_author_guid': first_author_guid,
              'first_author': first_author}
    
    response.title = "Select Merge Target - Montag"

    if search_form.validate(formname='search', session=None, request_vars=request.vars, message_onsuccess='',
                            keepvalues=True):

        author_to_search_for = read_form_field(search_form, 'query')
        retval['query'] = read_form_field(search_form, 'query')
    else:
        author_to_search_for = first_author['name']
        retval['query'] = author_to_search_for

    if len(author_to_search_for) > 0:
        # noinspection PyAugmentAssignment
        if author_to_search_for[0] != '%':
            author_to_search_for = '%' + author_to_search_for
        if author_to_search_for[-1] != '%':
            author_to_search_for += '%'

    page_number = 0
            
    if 'page' in request.vars:
        page_number = int(request.vars.page)
            
    search_forms.pass_paged_author_query_results_to_view(pdb, author_to_search_for, retval, page_number)

    retval['form'] = search_form
    retval['request'] = request

    return retval


def _fetch_tomes_by_author(author_id):
    tomes = pdb.get_tomes_by_author(author_id)
    tomes.sort(key=lambda x: x['title'])

    tomelist = []
    for tome in tomes:
        if tome['author_link_fidelity'] >= network_params.Min_Relevant_Fidelity:
            tome = pdb.get_tome_document_by_guid(tome['guid'], keep_id=True, include_local_file_info=True,
                                                 include_author_detail=True)
            tomelist.append(tome)
    return tomelist


@auth.requires_login()
def confirm_merge_authors():
    first_author_guid = request.args[0]
    first_author = pdb.get_author_by_guid(first_author_guid)
    first_author_tomes = _fetch_tomes_by_author(first_author['id'])

    second_author_guid = request.args[1]
    second_author = pdb.get_author_by_guid(second_author_guid)
    second_author_tomes = _fetch_tomes_by_author(second_author['id'])
    
    if second_author is None:
        session.flash = "Author not found"
        redirect(URL('select_author_merge_partner', args=first_author_guid))
        return
     
    response.title = "Confirm Merge - Montag"
    
    return {'first_author': first_author, 'first_author_tomes': first_author_tomes,
            'second_author': second_author, 'second_author_tomes': second_author_tomes}
    

@auth.requires_login()
def execute_merge_authors():
    first_author_guid = request.args[0]
    second_author_guid = request.args[1]

    use_data_from_first = request.args[2]
    if use_data_from_first.lower() == "false":
        use_data_from_first = False

    if use_data_from_first:
        pdb.fuse_authors(second_author_guid, target_guid=first_author_guid)
    else:
        pdb.fuse_authors(first_author_guid, target_guid=second_author_guid)

    redirect(URL('default', 'view_author', args=first_author_guid))


def _select_tome_merge_partner_form(first_tome):
    form = SQLFORM.factory(Field('query', requires=IS_NOT_EMPTY(),
                                 default=db_str_to_form(first_tome['title']), label="Search for"),
                           submit_button='Search',
                           _method='GET')
    return form


@auth.requires_login()
def select_tome_merge_partner():
    first_tome_guid = request.args[0]
    first_tome = pdb.get_tome_document_by_guid(first_tome_guid, keep_id=True,
                                               include_local_file_info=False, include_author_detail=True)
    if first_tome is None:
        session.flash = "Tome not found"
        redirect(URL('default', 'tomesearch'))
        return 

    search_form = _select_tome_merge_partner_form(first_tome)

    retval = {'first_tome_guid': first_tome_guid,
              'first_tome': first_tome
              }

    response.title = "Select Merge Target - Montag"
    page_number = 0
    
    if search_form.validate(formname='search', session=None, request_vars=request.vars, message_onsuccess='',
                            keepvalues=True):

        search_query = search_forms.build_search_query(search_form)
        if 'page' in request.vars:
            page_number = int(request.vars.page)
        retval['query'] = read_form_field(search_form, 'query')
    else:
        search_query = first_tome['title']
        retval['query'] = search_query
        
    search_forms.pass_paged_query_results_to_view(pdb, search_query, retval, page_number)

    retval['form'] = search_form
    retval['request'] = request

    return retval


@auth.requires_login()
def confirm_merge_tomes():
    first_tome_guid = request.args[0]
    first_tome = pdb.get_tome_document_by_guid(first_tome_guid, keep_id=True, include_local_file_info=True,
                                               include_author_detail=True)

    second_tome_guid = request.args[1]
    second_tome = pdb.get_tome_document_by_guid(second_tome_guid, keep_id=True, include_local_file_info=True,
                                                include_author_detail=True)
    
    if second_tome is None:
        session.flash = "Tome not found"
        redirect(URL('select_tome_merge_partner', args=first_tome_guid))
        return

    response.title = "Confirm Merge - Montag"
    
    return {'first_tome': first_tome, 'second_tome': second_tome}


@auth.requires_login()
def execute_merge_tomes():
    first_tome_guid = request.args[0]
    second_tome_guid = request.args[1]

    use_data_from_first = request.args[2]
    if use_data_from_first.lower() == "false":
        use_data_from_first = False

    if use_data_from_first:
        source_guid = second_tome_guid
        target_guid = first_tome_guid
    else:
        source_guid = first_tome_guid
        target_guid = second_tome_guid

    try:
        pdb.fuse_tomes(source_guid, target_guid=target_guid)
    except KeyError:  # one or both tomes do not exit (anymore), do nothing as
        # the most probable cause is a merge that just happened
        pass

    redirect(URL('default', 'view_tome', args=first_tome_guid))
