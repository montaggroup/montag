def _select_author_merge_partner_form(first_author):
    form = SQLFORM.factory(
        Field('query',requires=IS_NOT_EMPTY(), default=db_str_to_form(first_author['name']), label="Search for"),
        submit_button='Search',
        _method = 'GET')
    return form



def select_author_merge_partner():
    first_author_guid = request.args[0]
    first_author = db.get_author_by_guid(first_author_guid)
    
    if first_author is None:
        session.flash = "Author not found"
        redirect(URL('default', 'tomesearch'))
        return 

    search_form = _select_author_merge_partner_form(first_author)
    
    retval = {'first_author_guid': first_author_guid,
              'first_author': first_author}
    
    response.title = "Select Merge Target - Montag"
    page_number = 0

    if search_form.validate(formname = 'search', session = None, request_vars=request.vars, message_onsuccess='', keepvalues=True):
        author_to_search_for = search_form.vars['query'].decode('utf-8')
        if 'page' in request.vars:
            page_number = int(request.vars.page)
        retval['query'] = search_form.vars['query']
    else:
        author_to_search_for = first_author['name']
        retval['query'] = author_to_search_for

    if len(author_to_search_for) > 0:
        if author_to_search_for[0]!='%':
            author_to_search_for='%'+author_to_search_for
        if author_to_search_for[-1]!='%':
            author_to_search_for=author_to_search_for+'%'
            
            
    _pass_paged_author_query_results_to_view(author_to_search_for, retval, page_number)

    retval['form'] = search_form
    retval['request'] = request

    return retval


def confirm_merge_authors():
    first_author_guid = request.args[0]
    first_author = db.get_author_by_guid(first_author_guid)

    second_author_guid = request.args[1]
    second_author = db.get_author_by_guid(second_author_guid)
    
    if second_author is None:
        session.flash = "Author not found"
        redirect(URL('select_author_merge_partner', args=(first_author_guid)))
        return
     
    response.title = "Confirm Merge - Montag"
    
    return {'first_author': first_author, 'second_author': second_author}
    

def execute_merge_authors():
    first_author_guid = request.args[0]
    first_author = db.get_author_by_guid(first_author_guid)

    second_author_guid = request.args[1]
    second_author = db.get_author_by_guid(second_author_guid) 

    use_data_from_first = request.args[2]
    if use_data_from_first.lower()=="false":
        use_data_from_first = False


    if first_author_guid < second_author_guid:
        first_author_guid, second_author_guid = second_author_guid, first_author_guid
        first_author, second_author = second_author, first_author
        use_data_from_first = not use_data_from_first

    source_author = first_author if use_data_from_first else second_author

    new_author_doc = db.get_author_document_by_guid(first_author_guid)
    new_author_doc['fusion_sources'].append({'source_guid': second_author_guid, 'fidelity':  pydb.network_params.Default_Manual_Fidelity})
    if not use_data_from_first: # copy data from secnd entry over
        for key,value in source_author.iteritems():
            if key in new_author_doc:
                if key.lower() != "guid":
                    new_author_doc[key]=source_author[key]

    db.load_own_author_document(new_author_doc)
    redirect(URL('default','view_author', args=(first_author_guid)))

def _select_tome_merge_partner_form(first_tome):
    form = SQLFORM.factory(
        Field('query',requires=IS_NOT_EMPTY(), default=db_str_to_form(first_tome['title']), label="Search for"),
        submit_button='Search',
        _method = 'GET')
    return form


def select_tome_merge_partner():
    first_tome_guid = request.args[0]
    first_tome = db.get_tome_by_guid(first_tome_guid)
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
    
    if search_form.validate(formname = 'search', session = None, request_vars=request.vars, message_onsuccess='', keepvalues=True):
        search_query = _build_search_query(search_form)
        if 'page' in request.vars:
            page_number = int(request.vars.page)
        retval['query'] = search_form.vars['query'].decode('utf-8')
    else:
        search_query = first_tome['title']
        retval['query'] = search_query
        
    _pass_paged_query_results_to_view(search_query, retval, page_number)

    retval['form'] = search_form
    retval['request'] = request


    return retval


def confirm_merge_tomes():
    first_tome_guid = request.args[0]
    first_tome = db.get_tome_document_with_local_overlay_by_guid(first_tome_guid, include_local_file_info=True, include_author_detail=True)

    second_tome_guid = request.args[1]
    second_tome = db.get_tome_document_with_local_overlay_by_guid(second_tome_guid, include_local_file_info=True, include_author_detail=True)
    
    if second_tome is None:
        session.flash = "Tome not found"
        redirect(URL('select_tome_merge_partner', args=(first_tome_guid)))
        return
    
    
    response.title = "Confirm Merge - Montag"
    
    return {'first_tome': first_tome, 'second_tome': second_tome}


def execute_merge_tomes():
    first_tome_guid = request.args[0]

    second_tome_guid = request.args[1]

    use_data_from_first = request.args[2]
    if use_data_from_first.lower()=="false":
        use_data_from_first = False
    
    if use_data_from_first:
        db.fuse_tomes(second_tome_guid, target_guid=first_tome_guid)
    else:
        db.fuse_tomes(first_tome_guid, target_guid=second_tome_guid)

    redirect(URL('default','view_tome', args=(first_tome_guid)))
