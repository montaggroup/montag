# -*- coding: utf-8 -*-
if False:
    from pydb_helpers.ide_fake import *

import os
import subprocess
import cStringIO
import tempfile
import json
import re

from pydb import FileType, TomeType
from pydb import title
from pydb import pyrosetup
from pydb import ebook_metadata_tools
from pydb import network_params
from pydb_helpers.pydb_functions import db_str_to_form, read_form_field
from pydb_helpers.html_helpers import generate_download_filename
from pydb_helpers import search_forms


@auth.requires_login()
def getfile():
    tome_id = request.args[0]
    file_hash = request.args[1]

    tome_file = pdb.get_tome_file(tome_id, file_hash)

    fp = pyrosetup.fileserver().get_local_file_path(file_hash)
    plain_file = open(fp, "rb")

    return _stream_tome_file(tome_id, tome_file, plain_file)


@auth.requires_login()
def getfile_as_mobi():
    tome_id = request.args[0]
    file_hash = request.args[1]
    return _get_converted_file(tome_id, file_hash, 'mobi')


@auth.requires_login()
def getfile_as_epub():
    tome_id = request.args[0]
    file_hash = request.args[1]
    return _get_converted_file(tome_id, file_hash, 'epub')


@auth.requires_login()
def getfile_as_pdf():
    tome_id = request.args[0]
    file_hash = request.args[1]
    return _get_converted_file(tome_id, file_hash, 'pdf')


def _get_converted_file(tome_id, file_hash, target_extension):
    """ requires a calibre installation
    """
    session.forget(response)

    tome_file = pdb.get_tome_file(tome_id, file_hash)
    extension = tome_file['file_extension']

    fp = pyrosetup.fileserver().get_local_file_path(file_hash)
    with open(fp, "rb") as source_file:
        if extension == target_extension:
            return _stream_tome_file(tome_id, tome_file, source_file)
        else:
            contents = source_file.read()

    converted_content = _convert_ebook(contents, extension, target_extension)
    tome_file['file_extension'] = target_extension
    
    return _stream_tome_file(tome_id, tome_file, converted_content)
  

def _convert_ebook(contents, source_extension, target_extension):
    """ returns a cStringIO buffer with the conversion result, contents should be an buffer """

    # write into a temp file as to prevent ebook_convert from accessing the file store directly
    # this way we are sure that the file has the correct extension
    fd_orig, path_orig = tempfile.mkstemp('.' + source_extension)
    with os.fdopen(fd_orig, 'wb') as orig_file:
        orig_file.write(contents)

    fd_target, path_converted = tempfile.mkstemp('.'+target_extension)
    os.close(fd_target)
    
    subprocess.call(['ebook-convert', path_orig, path_converted])

    with open(path_converted, 'rb') as converted_file:
        converted_content = cStringIO.StringIO(converted_file.read())

    os.remove(path_orig)
    os.remove(path_converted)
     
    return converted_content
    

def _stream_tome_file(tome_id, tome_file, contents_stream):
    tome = pdb.get_tome(tome_id)
    tome_doc = pdb.get_tome_document_by_guid(tome['guid'])

    author_docs = [pdb.get_author_document_by_guid(author['guid']) for author in tome_doc['authors']]

    enriched_file = cStringIO.StringIO()
    added = ebook_metadata_tools.add_plain_metadata(contents_stream, tome_file, enriched_file, author_docs, tome_doc)
    if not added:  # use the file stream just as was passed, no metadata could be added.
        enriched_file = cStringIO.StringIO(contents_stream.read())

    enriched_file.seek(0, os.SEEK_END)
    file_size = enriched_file.tell()
    enriched_file.seek(0)

    filename = generate_download_filename(tome, tome_file)
    
    # \note: the kindle paperwhite only accepts our download
    # if we stream it in chucks and omit the content-length header
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Length'] = file_size
    response.headers['Content-Disposition'] = u'attachment;filename="{}"'.format(filename).encode('utf-8')

    return response.stream(enriched_file, chunk_size=20000)


@auth.requires_login()
def get_cover():
    tome_id = request.args[0]

    tome_file = pdb.get_best_relevant_cover_available(tome_id)
    if tome_file is None:
        return
    
    file_hash = tome_file['hash']
    
    fp = pyrosetup.fileserver().get_local_file_path(file_hash)
    if fp is None:
        return
    plain_file = open(fp, "rb")

    # \todo determine mime type and other image params
    # response.headers['Content-Type'] = 'image/jpeg'

    return response.stream(plain_file, chunk_size=20000)


@auth.requires_login()
def timeline():
    items_per_page = 20

    page_number = 0
    if 'page' in request.vars:
        page_number = int(request.vars.page)
    
    page_start = page_number * items_per_page
    page_end = (page_number+1) * items_per_page
    number_results_total = pdb.get_tome_document_timeline_size()

    changed_tome_guids = pdb.get_tome_document_timeline(items_per_page, page_start)
    
    response.title = "Timeline - Montag"
    tomelist = []
    for tome_index, tome_guid in enumerate(changed_tome_guids):
        tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True, include_local_file_info=True,
                                             include_author_detail=True)
        if 'title' in tome:
            tome['index'] = tome_index+1
            tomelist.append(tome)

    return {
        'tome_info': tomelist,
        'title': 'Timeline',
        'page': page_number,
        'page_start': page_start,
        'page_end': page_end,
        'number_results_total': number_results_total
    }


@auth.requires_login()
def random_tomes():
    response.title = "Random Tomes - Montag"
    
    tomes = pdb.get_random_tomes(20)
    tomelist = []
    for tome_index, tome_info in enumerate(tomes):
        tome = pdb.get_tome_document_by_guid(tome_info['guid'], include_local_file_info=True,
                                             include_author_detail=True, keep_id=True)
        tome['index'] = tome_index+1
        tomelist.append(tome)

    return {
        'tome_info': tomelist, 'title': 'Random Tomes'
    }


@auth.requires_login()
def timeline_json():
    result = timeline()
    return json.dumps(result['tome_info'])


@auth.requires_login()
def view_author():
    author_guid = request.args[0]

    author = pdb.get_author_by_guid(author_guid)
    if author is None:
        author_guid = pdb.get_author_fusion_target_guid(author_guid)
        if author_guid:
            redirect(URL('view_author', args=author_guid))
        
    tomes = pdb.get_tomes_by_author(author['id'])
    tomes.sort(key=lambda x: x['title'])

    response.title = u'{} - Montag'.format(author['name'])

    tomelist = []
    for tome in tomes:
        if tome['author_link_fidelity'] >= network_params.Min_Relevant_Fidelity:
            tome = pdb.get_tome_document_by_guid(tome['guid'], keep_id=True,
                                                 include_local_file_info=True, include_author_detail=True)
            tomelist.append(tome)

    return {
        'author_info':  author,
        'tome_info': tomelist
    }


@auth.requires_login()
def view_tome():
    tome_guid = request.args[0]
    
    tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True,
                                         include_local_file_info=True, include_author_detail=True)
    if 'title' not in tome:
        tome_guid = pdb.get_tome_fusion_target_guid(tome_guid)
        if tome_guid:
            redirect(URL('view_tome', args=tome_guid))

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"{} - Montag".format(title_text)

    return {
        'tome': tome
    }


@auth.requires_login()
def view_tome_debug_info():
    tome_guid = request.args[0]
    
    tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True,
                                         include_local_file_info=True, include_author_detail=True)
    debug_info = pdb.get_debug_info_for_tome_by_guid(tome_guid)
    
    friends = debug_info['friends']
    for friend_id, data in friends.iteritems():
        debug_info[u'friend_{}'.format(friend_id)] = data
        
    del debug_info['friends']
    
    return {
        'tome': tome,
        'enhanced_debug_info': debug_info
    }


def _author_edit_form(author, required_fidelity):
    form = SQLFORM.factory(Field('name', requires=IS_NOT_EMPTY(), default=db_str_to_form(author['name']),
                                 comment=XML(r'<input type="button" value="Guess name case" '
                                             r'onclick="title_case_field(&quot;no_table_name&quot;)">')),
                           Field('date_of_birth', default=author['date_of_birth'],
                                 comment=TOOLTIP('Please enter the date in ISO&nbsp;8601, '
                                                 'e.g. 1920-08-22. If only the year is known, use that.')),
                           Field('date_of_death', default=author['date_of_death'],
                                 comment=TOOLTIP('Please enter the date in ISO&nbsp;8601, '
                                                 'e.g. 1993-02-21. If only the year is known, use that.')),
                           Field('fidelity', requires=FidelityValidator(), default=required_fidelity,
                                 comment='Current Value: {}'.format(author['fidelity'])),
                           submit_button='Save')
    return form


@auth.requires_login()
def edit_author():
    author_guid = request.args[0]
    author_doc = pdb.get_author_document_by_guid(author_guid, keep_id=True)
    if 'name' not in author_doc:
        session.flash = "No such author"
        redirect(URL('tomesearch'))
        
    required_fidelity = pdb.calculate_required_author_fidelity(author_doc['id'])

    form = _author_edit_form(author_doc, required_fidelity)
    response.title = u'Edit {} - Montag'.format(author_doc['name'])

    if form.process(keepvalues=True, session=None).accepted:
        field_names = ['name', 'date_of_birth', 'date_of_death', 'fidelity']
        for f in field_names:
            author_doc[f] = read_form_field(form, f)

        pdb.load_own_author_document(author_doc)
        author_doc = pdb.get_author_document_by_guid(author_guid, keep_id=True)
        response.flash = 'Stored new values'
        redirect(URL('view_author', args=[author_guid]))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form, author=author_doc, required_fidelity=required_fidelity)


def _is_tome_or_author_guid(string):
    return re.match("[0-9a-z]{32}", string)


@auth.requires_login()
def tomesearch():
    retval = {}
    form = search_forms.build_search_form(pdb)

    if form.validate(formname='search', session=None, request_vars=request.vars, message_onsuccess='', keepvalues=True):
        query = read_form_field(form, 'query').strip()
        if _is_tome_or_author_guid(query):
            tome = pdb.get_tome_by_guid(query)
            if tome is not None:
                redirect(URL('view_tome', args=[query]))
                
            author = pdb.get_author_by_guid(query)
            if author is not None:
                redirect(URL('view_author', args=[query]))

        response.title = "Search Results - Montag"
        search_query = search_forms.build_search_query(form)

        page_number = 0
        if 'page' in request.vars:
            page_number = int(request.vars.page)
        search_forms.pass_paged_query_results_to_view(pdb, search_query, retval, page_number)

    retval['form'] = form
    retval['query'] = read_form_field(form, 'query')
    retval['request'] = request
        
    return retval


def _tome_edit_form(tome, required_tome_fidelity):
    form = SQLFORM.factory(Field('title', requires=IS_NOT_EMPTY(), default=db_str_to_form(tome['title']),
                                 comment=DIV(
                           TOOLTIP('Please enter the title of the book like it is written on the cover.'),
                           XML(r'<input type="button" value="Guess title case" onclick="title_case_field(&quot;no_table_title&quot;)">'),
                               _class='nowrap')),
                           Field('subtitle', default=db_str_to_form(tome['subtitle']),
                                 comment=XML(r'<input type="button" value="Guess subtitle case" onclick="title_case_field(&quot;no_table_subtitle&quot;)">')),
                           Field('edition', default=db_str_to_form(tome['edition'])),
                           Field('principal_language', default=db_str_to_form(tome['principal_language']),
                                 comment=TOOLTIP('Please use two letter ISO 639-1 codes (e.g. en for English).')),
                           Field('publication_year', default=db_str_to_form(tome['publication_year'])),
                           Field('tags', 'text', default=tome['tags'], requires=TagValidator()),
                           Field('type', default=tome['type'], widget=SQLFORM.widgets.radio.widget,
                                 requires=IS_IN_SET({TomeType.Fiction: 'fiction', TomeType.NonFiction: 'non-fiction'})),
                           Field('fidelity', requires=FidelityValidator(), default=required_tome_fidelity,
                                 comment='Current Value: {}'.format(tome['fidelity'])),
                           submit_button='Save',
                           name="edit_tome")

    return form


def _tome_synopses_form(synopsis):
    form = SQLFORM.factory(Field('content', 'text', default=db_str_to_form(synopsis['content'])),
                           Field('fidelity', requires=FidelityValidator(), default=synopsis['fidelity']+0.1),
                           hidden={'guid': synopsis['guid'], '_formname': 'edit_synopsis_{}'.format(synopsis['guid'])},
                           submit_button='Save')
    return form


@auth.requires_login()
def add_synopsis_to_tome():
    tome_guid = request.args[0]
    tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True,
                                         include_local_file_info=True, include_author_detail=True)
    
    new_syn = {'guid': pdb.generate_guid(),
               'fidelity': network_params.Default_Manual_Fidelity,
               'content': ""
               }
    tome['synopses'].append(new_syn)
    
    return _edit_tome(tome)
    

@auth.requires_login()
def edit_tome():
    tome_guid = request.args[0]
    tome_doc = pdb.get_tome_document_by_guid(tome_guid, keep_id=True,
                                             include_local_file_info=True, include_author_detail=True)
    if tome_doc is None:
        session.flash = "No such tome"
        redirect(URL('tomesearch'))
    return _edit_tome(tome_doc)
    

def _edit_tome(tome_doc):
    if not tome_doc:
        return "Tome no longer existing!"

    title_text = title.coalesce_title(tome_doc['title'], tome_doc['subtitle'])
    response.title = u"Edit {} - Montag".format(title_text)

    field_names = ['title', 'subtitle', 'edition', 'principal_language', 'publication_year', 'tags', 'type', 'fidelity']
    syn_field_names = ['content', 'fidelity']
    
    tome_id = tome_doc['id']
    required_tome_fidelity = pdb.calculate_required_tome_fidelity(tome_id)

    form = _tome_edit_form(tome_doc, required_tome_fidelity)
    synforms = list()
    
    relevant_synopses = list(network_params.relevant_items(tome_doc['synopses']))
    tome_doc['synopses'] = relevant_synopses
    for synopsis in relevant_synopses:
        synforms.append(_tome_synopses_form(synopsis))
        
    if 'guid' in request.vars:
        synopsis_guid = request.vars.guid
        formname = u'edit_synopsis_{}'.format(synopsis_guid)

        for syn_idx, synform in enumerate(synforms):
            if synform.process(session=None, formname=formname, keepvalues=True).accepted:
                if not synopsis_guid:
                    raise ValueError("No synopsis guid found")
                
                for synopsis in tome_doc['synopses']:
                    if synopsis['guid'] == synopsis_guid:
                        synopsis_to_edit = synopsis
                        break
                else:
                    synopsis_to_edit = {'guid': synopsis_guid}
                    tome_doc['synopses'].append(synopsis_to_edit)
    
                for sf in syn_field_names:
                    synopsis_to_edit[sf] = read_form_field(synform, sf)
                pdb.load_own_tome_document(tome_doc)
                redirect(URL('edit_tome', args=(tome_doc['guid']), anchor='synopses'))

            elif synform.errors:
                response.flash = 'form has errors'
    
    if form.process(session=None, formname='edit_tome', keepvalues=True).accepted:
        for f in field_names:
            tome_doc[f] = read_form_field(form, f)
        if 'authors' not in tome_doc:
            tome_doc['authors'] = []
        if 'files' not in tome_doc:
            tome_doc['files'] = []
        if 'publication_year' not in tome_doc:
            tome_doc['publication_year'] = None
        elif tome_doc['publication_year'] == 'None':
            tome_doc['publication_year'] = None
        pdb.load_own_tome_document(tome_doc)
        redirect(URL('view_tome', args=(tome_doc['guid'])))

    elif form.errors:
        response.flash = 'form has errors'
    
    tome_doc['id'] = tome_id
    return dict(form=form, tome=tome_doc, tome_id=tome_id, synforms=synforms, required_fidelity=required_tome_fidelity)


@auth.requires_login()
def edit_tome_file_link():
    tome_id = request.args[0]
    file_hash = request.args[1]
    tome = pdb.get_tome(tome_id)

    files = pdb.get_tome_files(tome_id, include_local_file_info=True)
    tome_files = filter(lambda x: x['hash'] == file_hash, files)
    tome_file = tome_files[0]

    form = SQLFORM.factory(Field('file_extension', default=db_str_to_form(tome_file['file_extension'])),
                           Field('fidelity', requires=FidelityValidator(), default=tome_file['fidelity']+0.1),
                           submit_button='Save')

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"Edit Files {} - Montag".format(title_text)
    
    field_names = ['file_extension', 'fidelity']

    if form.process(keepvalues=True).accepted:
        doc = pdb.get_tome_document_by_guid(tome['guid'])
        other_files = filter(lambda x: x['hash'] != file_hash, doc['files'])
        tome_file_doc = filter(lambda x: x['hash'] == file_hash, doc['files'])[0]

        for f in field_names:
            tome_file_doc[f] = read_form_field(form, f)

        other_files.append(tome_file_doc)
        doc['files'] = other_files
        pdb.load_own_tome_document(doc)
            
        response.flash = 'Stored new values'
        redirect(URL('edit_tome', args=(tome['guid']), anchor='files'))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form, tome=tome, file=tome_file)


@auth.requires_login()
def link_tome_to_file():
    tome_id = request.args[0]
    tome = pdb.get_tome(tome_id)
 
    form = SQLFORM.factory(Field('hash'),
                           Field('file_extension', default="epub"),
                           Field('fidelity', requires=FidelityValidator(), default=70),
                           submit_button='Save')

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u'Edit Files of {} - Montag'.format(title_text)
    
    if form.process(keepvalues=True).accepted:
    
        file_hash = read_form_field(form, 'hash')
        file_extension = read_form_field(form, 'file_extension')
        fidelity = read_form_field(form, 'fidelity')
        
        local_file_size = pyrosetup.fileserver().get_local_file_size(file_hash)
        
        if not local_file_size:
            response.flash = 'This file is not known to the database, please check the hash'
        else:
            pdb.link_tome_to_file(tome_id, file_hash, local_file_size, file_extension, FileType.Content, fidelity)
            session.flash = 'Added new file link'
            redirect(URL('edit_tome_file_link', args=(tome_id, file_hash)))
    elif form.errors:
        response.flash = 'form has errors'
        
    return dict(form=form, tome=tome)


@auth.requires_login()
def edit_tome_author_link():
    tome_id = request.args[0]
    author_id = request.args[1]
    
    tome = pdb.get_tome(tome_id)
       
    tome_authors = pdb.get_tome_authors(tome_id)
    for ta in tome_authors:
        if int(ta['id']) == int(author_id):
            tome_author = ta
            break
    else:
        return dict(error="Tome and author not linked?", form=None, tome=tome, author=None, authors=tome_authors)

    author_guid = tome_author['guid']
    
    form = SQLFORM.factory(Field('order', default=tome_author['author_order']),
                           Field('fidelity', requires=FidelityValidator(), default=tome_author['link_fidelity']+0.1),
                           submit_button='Save')

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"Edit Author Link {} <=>  {} - Montag".format(tome_author['name'], title_text)

    if form.process(keepvalues=True).accepted:
        doc = pdb.get_tome_document_by_guid(tome['guid'])
        other_authors = filter(lambda x: x['guid'] != author_guid, doc['authors'])
        tome_author_doc = filter(lambda x: x['guid'] == author_guid, doc['authors'])[0]

        for f in ('order', 'fidelity'):
            tome_author_doc[f] = read_form_field(form, f)

        other_authors.append(tome_author_doc)
        doc['authors'] = other_authors
        pdb.load_own_tome_document(doc)
        tome_authors = pdb.get_tome_authors(tome_id)

        response.flash = 'Stored new values'
        redirect(URL('edit_tome', args=(tome['guid']), anchor='authors'))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome, author=tome_author, authors=tome_authors)


@auth.requires_login()
def link_tome_to_author():
    tome_id = request.args[0]
    tome = pdb.get_tome(tome_id)

    tome_authors = pdb.get_tome_authors(tome_id)

    if tome_authors:
        last_tome_author = max(tome_authors, key=lambda x: float(x['author_order']))
        max_author_order = last_tome_author['author_order']
    else:
        max_author_order = 0
        
    form = SQLFORM.factory(Field('author_name'),
                           Field('order', default=max_author_order+1, label='Order Value'),
                           Field('fidelity', requires=FidelityValidator(), default=70),
                           submit_button='Save')

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"Add Author to {} - Montag".format(title_text)

    if form.process(keepvalues=True).accepted:

        author_name = read_form_field(form, 'author_name')
        fidelity = read_form_field(form, 'fidelity')
        author_order = float(read_form_field(form, 'order'))

        author_ids = pdb.find_or_create_authors([author_name], fidelity)
        author_id = author_ids[0]

        pdb.link_tome_to_author(tome_id, author_id, author_order, fidelity)

        session.flash = 'Added author to tome'
        redirect(URL('edit_tome', args=(tome['guid']), anchor='authors'))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome, authors=tome_authors)


@auth.requires_login()
def more_actions():
    response.title = "More Actions - Montag"
    return dict()


@auth.requires_login()
def index():
    redirect(URL('tomesearch'))
    return dict()


def user():
    return dict(form=auth())
