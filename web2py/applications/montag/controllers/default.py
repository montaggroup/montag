# -*- coding: utf-8 -*-
import os
import subprocess
import cStringIO
import time
from pydb import FileType, TomeType
import pydb.title
import pydb.ebook_metadata_tools
import tempfile
import json
import pydb.pyrosetup
import uuid

def getfile():
    tome_id = request.args[0]
    file_hash = request.args[1]

    tome_file = db.get_tome_file(tome_id, file_hash)
    print tome_file
    extension=tome_file['file_extension']

    fp = db.get_local_file_path(file_hash)
    plain_file = open(fp,"rb")

    return _stream_tome_file(tome_id, extension, plain_file)

def getfile_as_mobi():
    tome_id = request.args[0]
    file_hash = request.args[1]
    return _get_converted_file(tome_id, file_hash, 'mobi')

def getfile_as_epub():
    tome_id = request.args[0]
    file_hash = request.args[1]
    return _get_converted_file(tome_id, file_hash, 'epub')

def _get_converted_file(tome_id, file_hash, target_extension):
    """ requires a calibre installation
    """
    tome_id = request.args[0]
    file_hash = request.args[1]
    session.forget(response)

    tome_file = db.get_tome_file(tome_id, file_hash)
    extension=tome_file['file_extension']

    fp = db.get_local_file_path(file_hash)
    with open(fp,"rb") as source_file:
        if extension == target_extension:    
            return _stream_tome_file(tome_id, extension, source_file)
        else:
            contents = source_file.read()

    # write into a temp file as to prevent ebook_convert from accessing the file store directly
    # this way we are sure that the file has the correct extension
    fd_orig, path_orig=tempfile.mkstemp('.'+extension)
    orig_file=os.fdopen(fd_orig,'wb')
    orig_file.write(contents)
    del contents
    orig_file.close()
    
    fd_target, path_target=tempfile.mkstemp('.'+target_extension)
    os.close(fd_target)
    
    print "Converting {} to {}".format(path_orig, path_target)
    convert_result=subprocess.call(['ebook-convert',path_orig, path_target])
    print "cv is",convert_result
    converted_content = open(path_target, 'rb')
    
    return _stream_tome_file(tome_id, target_extension, converted_content)
    

def _stream_tome_file(tome_id, extension, contents_stream):
    # \todo error handling for tome or tome_file not found    
    tome = db.get_tome(tome_id)
    tome_doc = db.get_tome_document_by_guid(tome['guid'])

    author_docs = [db.get_author_document_by_guid(author['guid']) for author in tome_doc['authors']]

    title=  tome['title'].encode("ascii", errors='ignore')
    filename = '%s.%s' % (title, extension.encode('utf-8'))

    
    enriched_file = cStringIO.StringIO()
    added=pydb.ebook_metadata_tools.add_plain_metadata(contents_stream, extension, enriched_file, author_docs, tome_doc)
    if not added: #use the file stream just as was passed, no metadata could be added.
        enriched_file = contents_stream

    enriched_file.seek(0)
    
    enriched_file.seek(0, os.SEEK_END)
    file_size = enriched_file.tell()
    enriched_file.seek(0)
    
    
    # \note: the kindle paperwhite only accepts our download if we stream it in chucks and omit the content-length header 
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Length'] = file_size
    response.headers['Content-Disposition'] = 'attachment;filename="%s"' % filename

    return response.stream(enriched_file, chunk_size=20000)


def get_cover():
    tome_id = request.args[0]

    tome_file = db.get_best_relevant_cover_available(tome_id)
    if tome_file is None:
        return
    
    extension=tome_file['file_extension']
    file_hash=tome_file['hash']
    
    fp = db.get_local_file_path(file_hash)
    if fp is None:
        return
    plain_file = open(fp,"rb")

    # \todo determine mime type and other image params
    # response.headers['Content-Type'] = 'image/jpeg'

    return response.stream(plain_file, chunk_size=20000)


def timeline():
    history_days = 1
    tome_limit = 50
    
    min_modification_date_tomes = time.time()-history_days*3600*24
    min_modification_date_authors = time.time()+1000  # no authors

    changed_tome_guids = db.get_tome_document_timeline(tome_limit)
    
    response.title = "Timeline - Montag"
    tomelist = []
    for tome_index, tome_guid in enumerate(changed_tome_guids):
       tome = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info = True, include_author_detail=True)
       if 'title' in tome:
           tome['index'] = tome_index+1
           tomelist.append(tome)

    return {
        'tome_info': tomelist, 'title': 'Timeline'
    }

def random_tomes():
    response.title = "Random Tomes - Montag"
    
    tomes = db.get_random_tomes(20) 
    tomelist = []
    for tome_index, tome_info in enumerate(tomes):
        tome = db.get_tome_document_with_local_overlay_by_guid(tome_info['guid'], include_local_file_info = True, include_author_detail=True)
        tome['index'] = tome_index+1
        tomelist.append(tome)

    return {
        'tome_info': tomelist, 'title': 'Random Tomes'
    }

def timeline_json():
    result = timeline()
    return json.dumps(result['tome_info'])

def view_author():
    author_guid = request.args[0]

    author = db.get_author_by_guid(author_guid)
    if author is None:
        author_guid = db.get_author_fusion_target_guid(author_guid)
        if author_guid:
            redirect(URL('view_author', args=(author_guid)))
        
    tomes = db.get_tomes_by_author(author['id'])
    tomes.sort(key=lambda x: x['title'])

    response.title = "%s - Montag" % author['name']

    tomelist = []
    for tome in tomes:
        if tome['author_link_fidelity'] > pydb.network_params.Min_Relevant_Fidelity:
            tome = db.get_tome_document_with_local_overlay_by_guid(tome['guid'], include_local_file_info = True, include_author_detail=True)
            tomelist.append(tome)

    return {
        'author_info':  author,
        'tome_info': tomelist
    }

def view_tome():
    tome_guid = request.args[0]
    
    tome = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info=True, include_author_detail=True)
    if not 'title' in tome:
        tome_guid = db.get_tome_fusion_target_guid(tome_guid)
        if tome_guid:
            redirect(URL('view_tome', args=(tome_guid)))

    title_text=pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = "%s - Montag" % title_text

    return {
        'tome': tome
    }

def view_tome_debug_info():
    tome_guid = request.args[0]
    
    tome = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info=True, include_author_detail=True)
    debug_info = db.get_debug_info_for_tome_by_guid(tome_guid)
    
    overlay_tome = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info = True, include_author_detail=False)
    debug_info['overlay'] = overlay_tome


    friends = debug_info['friends']
    for friend_id, data in friends.iteritems():
        debug_info['friend_{}'.format(friend_id)] = data
        
    del debug_info['friends']
    
    return {
        'tome': tome,
        'enhanced_debug_info': debug_info
    }


def _author_edit_form(author):
   required_fidelity = db.calculate_required_author_fidelity(author['id'])
 
   form = SQLFORM.factory(
        Field('name',requires=IS_NOT_EMPTY(), default=db_str_to_form(author['name']), comment=XML(r'<input type="button" value="Guess name case" onclick="title_case_field(&quot;no_table_name&quot;)">')),
        Field('date_of_birth', default=author['date_of_birth'], comment='ISO 8601, e.g. 1920-08-22'),
        Field('date_of_death',default=author['date_of_death'], comment='ISO 8601, e.g. 2012-06-05'),
        Field('fidelity', default=str(required_fidelity).encode('utf-8'), comment='Current Value: {}'.format(author['fidelity'])),
        )
   return form


def edit_author():
    author_guid = request.args[0]
    author_doc = db.get_author_document_with_local_overlay_by_guid(author_guid)
    if author_doc is None:
        session.flash = "No such author"
        reditrect(URL('tomesearch'))

    field_names = ['name', 'date_of_birth', 'date_of_death', 'fidelity']

    form = _author_edit_form(author_doc)
    response.title = "Edit %s - Montag" % author_doc['name']

    if form.process(keepvalues=True).accepted:
        for f in field_names:
            author_doc[f] = form.vars[f].decode('utf-8')

        db.load_own_author_document(author_doc)
        author_doc = db.get_author_document_with_local_overlay_by_guid(author_guid)
        response.flash = 'Stored new values'
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form, author=author_doc)

def _is_tome_guid(string):
    return re.match("[0-9a-z]{32}", string)

def tomesearch():
    retval = {}
    form = _build_search_form()

    if form.validate(formname = 'search', session = None, request_vars=request.vars, message_onsuccess='', keepvalues=True):
        query = form.vars['query'].strip()
        if _is_tome_guid(query):
            tome = db.get_tome_by_guid(query)
            if tome is not None:
                redirect(URL('view_tome', args=[query]))
        
        
        response.title = "Search Results - Montag"
        search_query = _build_search_query(form)

        page_number = 0
        if 'page' in request.vars:
            page_number = int(request.vars.page)
        _pass_paged_query_results_to_view(search_query, retval, page_number)


    retval['form'] = form
    retval['query'] = form.vars['query']
    retval['request'] = request
        
    return retval

    
def _tome_edit_form(tome_id, tome):
    
    required_tome_fidelity = db.calculate_required_tome_fidelity(tome_id)
    form = SQLFORM.factory(
        Field('title',requires=IS_NOT_EMPTY(), default=tome['title'].encode('utf-8'), comment=XML(r'<input type="button" value="Guess title case" onclick="title_case_field(&quot;no_table_title&quot;)">')),
        Field('subtitle', default=db_str_to_form(tome['subtitle']), comment=XML(r'<input type="button" value="Guess subtitle case" onclick="title_case_field(&quot;no_table_subtitle&quot;)">')),
        Field('edition',default=db_str_to_form(tome['edition'])),
        Field('principal_language',default=db_str_to_form(tome['principal_language'])),
        Field('publication_year', default=str(tome['publication_year']).encode('utf-8')),
        Field('tags','text', default=tome['tags'], requires=tag_validator()),
        Field('type', default=tome['type'] , widget=SQLFORM.widgets.radio.widget, requires=IS_IN_SET({TomeType.Fiction:'fiction',TomeType.NonFiction:'non-fiction'})),
        Field('fidelity', default=str(required_tome_fidelity).encode('utf-8'), comment='Current Value: {}'.format(tome['fidelity'])),
        name="edit_tome"
        )

    return form


def _tome_synopses_form(synopsis):
    form = SQLFORM.factory(
        Field('content','text', default=synopsis['content'].encode('utf-8')),
        Field('fidelity', default=str(synopsis['fidelity']+0.1).encode('utf-8')),
        hidden={
                'guid': synopsis['guid'],
                '_formname':'edit_synopsis_{}'.format(synopsis['guid'])
        },
        )
    return form

class tag_validator:
    def __init__(self, format="a", error_message="b"):
        pass
        
    def __call__(self, field_value):
        used_tag_values=set()
        tags = []
        
        field_value=field_value.decode('utf-8')
        for line_index, line in enumerate(field_value.split("\n")):
            line=line.strip()
            if line:
                fidelity = pydb.network_params.Default_Manual_Fidelity
                value = line
                if " " in line:
                    (fidelity_string, value_string) = line.split(" ",1)
                    try:
                        fidelity = float(fidelity_string)
                        value = value_string
                    except ValueError:
                        pass
                
                value=value.strip()
                if value in used_tag_values:
                    return None,u"Duplicate tag names entered: {}".format(value)
                used_tag_values.add(value)
                tags.append({"fidelity":fidelity, "tag_value" : value})
        return tags, None
     
    def formatter(self, value):
        tags=value
        return "\n".join(["%.1f %s" %(tag['fidelity'], tag['tag_value'].encode('utf-8')) for tag in tags])

def add_synopsis_to_tome():
    tome_guid = request.args[0]
    tome = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info=True, include_author_detail=True)
    
    new_syn = {
               'guid' : db.generate_guid(),
               'fidelity': pydb.network_params.Default_Manual_Fidelity,
               'content': ""
               }
    tome['synopses'].append(new_syn)
    
    return _edit_tome(tome, is_add_synopsis=True)
    
    
def edit_tome():
    tome_guid = request.args[0]
    tome_doc = db.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info=True, include_author_detail=True)
    if tome_doc is None:
        session.flash = "No such tome"
        redirect(URL('tomesearch'))
    return _edit_tome(tome_doc)
    

def _edit_tome(tome_doc, is_add_synopsis=False):
    if not tome_doc:
        return "Tome no longer existing!"

    title_text=pydb.title.coalesce_title(tome_doc['title'], tome_doc['subtitle'])
    response.title = u"Edit {} - Montag".format(title_text)

    field_names=['title','subtitle','edition','principal_language','publication_year','tags','type','fidelity']
    syn_field_names=['content','fidelity']
    
    tome_id = tome_doc['id']
    form= _tome_edit_form(tome_id, tome_doc)
    synforms = list()
    
    relevant_synopses = filter(lambda f: f['fidelity'] >  pydb.network_params.Min_Relevant_Fidelity, tome_doc['synopses'])
    tome_doc['synopses'] = relevant_synopses
    for synopsis in relevant_synopses:
        synforms.append(_tome_synopses_form(synopsis))
        
    if 'guid' in request.vars:
        synopsis_guid = request.vars.guid
        formname = u'edit_synopsis_{}'.format(synopsis_guid)

        for syn_idx, synform in enumerate(synforms):
            if synform.process(session = None, formname=formname, keepvalues=True).accepted:
                if not synopsis_guid:
                    raise ValueError("No synopsis guid found")
                
                for synopsis in tome_doc['synopses']:
                    if synopsis['guid'] == synopsis_guid:
                        synopsis_to_edit = synopsis
                        break
                else:
                    synopsis_to_edit = {'guid': synopsis_guid }
                    tome_doc['synopses'].append(synopsis_to_edit)
    
                for sf in syn_field_names:
                    synopsis_to_edit[sf]=synform.vars[sf].decode('utf-8')
                db.load_own_tome_document(tome_doc)
                redirect(URL('edit_tome', args=(tome_doc['guid']), anchor= 'synopses'))

            elif synform.errors:
                response.flash = 'form has errors'
    
    if form.process(session = None, formname='edit_tome', keepvalues=True).accepted:
        for f in field_names:
            if f == 'tags':
                tome_doc[f] = form.vars[f]
            else:
                tome_doc[f] = form.vars[f].decode('utf-8')
        if not 'authors' in tome_doc:
            tome_doc['authors']=[]
        if not 'files' in tome_doc:
            tome_doc['files']=[]
        if not 'publication_year' in tome_doc:
            tome_doc['publication_year']=None
        elif tome_doc['publication_year']=='None':
            tome_doc['publication_year']=None
        db.load_own_tome_document(tome_doc)
        redirect(URL('edit_tome', args=(tome_doc['guid'])))

    elif form.errors:
        response.flash = 'form has errors'
    
    tome_doc['id']=tome_id
    return dict(form=form, tome=tome_doc, tome_id=tome_id, synforms=synforms)


def edit_tome_file_link():
    tome_id=request.args[0]
    file_hash=request.args[1]
    tome=db.get_tome(tome_id)

    files = db.get_tome_files( tome_id, include_local_file_info = True)
    tome_files=filter( lambda x: x['hash']==file_hash, files)
    tome_file=tome_files[0]

    form = SQLFORM.factory(
        Field('file_extension', default=tome_file['file_extension'].encode('utf-8')),
        Field('fidelity', default=tome_file['fidelity']+0.1)
    )

    title_text=pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = "Edit Files %s - Montag" % title_text
    
    field_names=['file_extension','fidelity']

    if form.process(keepvalues=True).accepted:
        doc=db.get_tome_document_with_local_overlay_by_guid(tome['guid'])
        other_files=filter( lambda x: x['hash']!=file_hash, doc['files'])
        tome_file_doc=filter( lambda x: x['hash']==file_hash, doc['files'])[0]

        for f in field_names:
            if f == 'file_extension':
                tome_file_doc[f] = form.vars[f].decode('utf-8')
            else:
                tome_file_doc[f] = form.vars[f]

        other_files.append(tome_file_doc)
        doc['files']=other_files    
        db.load_own_tome_document(doc)
            
        response.flash = 'Stored new values'
        redirect(URL('edit_tome', args=(tome['guid']), anchor='files'))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form, tome=tome,file=tome_file)


def link_tome_to_file():
    tome_id=request.args[0]
    tome=db.get_tome(tome_id)
 
    form = SQLFORM.factory(
        Field('hash'),
        Field('file_extension', default="epub"),
        Field('fidelity', default=70)        
    )
    
    title_text=pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = "Edit Files %s - Montag" % title_text
    
    if form.process(keepvalues=True).accepted:
    
        file_hash=form.vars['hash']
        file_extension=form.vars['file_extension']
        fidelity=form.vars['fidelity']
        
        local_file_size=db.get_local_file_size(file_hash)
        
        if not local_file_size:
            response.flash = "This file is not known to the database, please check the hash"
        else:
            db.link_tome_to_file(tome_id, file_hash, local_file_size, file_extension, FileType.Content, fidelity)
            session.flash = 'Added new file link'
            redirect(URL('edit_tome_file_link', args=(tome_id, file_hash)))
    elif form.errors:
        response.flash = 'form has errors'
        
    return dict(form=form, tome=tome)

def edit_tome_author_link():
    tome_id=request.args[0]
    author_id=request.args[1]
    
    tome=db.get_tome(tome_id)
       
    tome_authors = db.get_tome_authors(tome_id)
    tome_author = None
    for ta in tome_authors:
        if int(ta['id'])==int(author_id):
            tome_author = ta
    
    if tome_author is None:
        return dict( error="Tome and author not linked?", form=None, tome=tome, author=None, authors=tome_authors)
    author_guid=tome_author['guid']
    
    form = SQLFORM.factory(
        Field('order', default=tome_author['author_order']),
        Field('fidelity', default=tome_author['link_fidelity']+0.1)
    )

    title_text=pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = "Edit Author Link %s <=>  %s - Montag" % (tome_author['name'], title_text)
    
    field_names=['order','fidelity']

    if form.process(keepvalues=True).accepted:
        doc=db.get_tome_document_with_local_overlay_by_guid(tome['guid'])
        other_authors=filter( lambda x: x['guid']!=author_guid, doc['authors'])
        tome_author_doc=filter( lambda x: x['guid']==author_guid, doc['authors'])[0]

        for f in field_names:
            tome_author_doc[f]=form.vars[f]

        other_authors.append(tome_author_doc)
        doc['authors']=other_authors
        db.load_own_tome_document(doc)
        tome_authors = db.get_tome_authors(tome_id)

        response.flash = 'Stored new values'
        redirect(URL('edit_tome', args=(tome['guid']), anchor='authors'))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome, author = tome_author, authors=tome_authors)


def link_tome_to_author():
    tome_id=request.args[0]
    tome=db.get_tome(tome_id)

    tome_authors = db.get_tome_authors(tome_id)

    if tome_authors:
        last_tome_author = max(tome_authors, key=lambda x: float(x['author_order']))
        max_author_order = last_tome_author['author_order']
    else:
        max_author_order = 0
        
    form = SQLFORM.factory(
        Field('author_name'),
        Field('order', default=max_author_order+1, label='Order Value'),
        Field('fidelity', default=70)
    )

    title_text=pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = "Add Author to %s - Montag" % title_text

    if form.process(keepvalues=True).accepted:

        author_name=form.vars['author_name'].decode('utf-8')
        fidelity=float(form.vars['fidelity'])
        author_order=float(form.vars['order'])

        author_ids = db.find_or_create_authors([author_name],fidelity)
        author_id = author_ids[0]

        db.link_tome_to_author(tome_id, author_id, author_order, fidelity)

        session.flash = 'Added author to tome'
        redirect(URL('edit_tome_author_link', args=(tome_id, author_id)))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome, authors=tome_authors)

def more_actions():
    response.title = "More Actions - Montag"
    return dict()

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    response.flash = "Welcome to web2py!"
    redirect(URL('tomesearch'))
    return dict() #(message=T('Hello World'))


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()
