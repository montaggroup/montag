# coding: utf8
if False:
    from pydb_helpers.ide_fake import *

import tempfile
import os

import pydb.ebook_metadata_tools
from pydb import FileType
from pydb import network_params
from pydb_helpers.pydb_functions import read_form_field
from pydb import title
from pydb import pyrosetup
from pydb import ebook_metadata_tools


@auth.requires_login()
def edit_covers():
    tome_id = request.args[0]
    tome = pdb.get_tome(tome_id)
    tome_guid = tome['guid']

    tome = pdb.get_tome_document_by_guid(tome_guid, include_local_file_info=True,
                                         include_author_detail=True, keep_id=True)

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u'Edit Cover for {} - Montag'.format(title_text)

    available_covers = []
    available_content = []

    relevant_files = network_params.relevant_items(tome['files'])
    relevant_local_files = filter(lambda f: f['has_local_copy'], relevant_files)

    for tome_file in relevant_local_files:
        if tome_file['file_type'] == pydb.FileType.Content:
            if tome_file['file_extension'] != 'txt':
                available_content.append(tome_file)
        elif tome_file['file_type'] == pydb.FileType.Cover:
            available_covers.append(tome_file)
        else:
            raise ValueError('Invalid value for file type')

    locally_available_covers = filter(lambda x: x['has_local_copy'], available_covers)
    
    if locally_available_covers:
        current_cover = max(locally_available_covers, key=lambda x: x['fidelity'])
    else:
        current_cover = None
        
    return {'tome': tome, 'available_covers': available_covers,
            'available_content': available_content, 'current_cover': current_cover}


@auth.requires_login()
def edit_covers_compact():
    return edit_covers()


def _set_cover_from_content_form():
    default_cover_fidelity = 80
    form = SQLFORM.factory(Field('fidelity', requires=FidelityValidator(), default=default_cover_fidelity),
                           submit_button='Save')
    return form


@auth.requires_login()
def set_cover_from_content():
    tome_id = request.args[0]
    content_hash = request.args[1]
    content_extension = request.args[2]
    only_display_cover_afterwards = request.args[3]
    if only_display_cover_afterwards.lower() == 'false':
        only_display_cover_afterwards = False

    tome = pdb.get_tome(tome_id)
    form = _set_cover_from_content_form()

    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u'Set Cover for {} - Montag'.format(title_text)

    if form.process(keepvalues=True).accepted:
        fidelity = read_form_field(form, 'fidelity')
        cover_contents = _extract_image_from_content(content_hash, content_extension)
        if cover_contents is None:
            session.flash('Cover could not be loaded - sorry!')
            redirect(URL('default', 'view_tome', args=(tome['guid'])))
            return

        file_extension = 'jpg'
        fd_cover, path_cover = tempfile.mkstemp('.' + file_extension)
        with os.fdopen(fd_cover, 'wb') as cover_file:
            cover_file.write(cover_contents.getvalue())

        file_server = pyrosetup.fileserver()
        (local_file_id, file_hash, file_size) = file_server.add_file_from_local_disk(path_cover, file_extension,
                                                                                     move_file=True)
        
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Cover, fidelity)
        if only_display_cover_afterwards:
            redirect(URL('covers', 'get_cover_image', args=(file_hash, file_extension)))
        else:
            redirect(URL('default', 'view_tome', args=(tome['guid'])))

    return {'tome': tome, 'content_hash': content_hash, 'content_extension': content_extension, 'form': form}


def _set_main_cover_form():
    default_cover_fidelity = 80
    # \todo use a more sensible value for fidelity
    form = SQLFORM.factory(Field('fidelity', requires=FidelityValidator(), default=default_cover_fidelity),
                           submit_button='Save')
    return form


@auth.requires_login()
def set_main_cover():
    tome_id = request.args[0]
    file_hash = request.args[1]
    file_extension = request.args[2]

    tome = pdb.get_tome(tome_id)
    form = _set_main_cover_form()
    
    title_text = title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u'Set Cover for {} - Montag'.format(title_text)

    file_size = pyrosetup.fileserver().get_local_file_size(file_hash)

    if form.process(keepvalues=True).accepted:
        fidelity = read_form_field(form, 'fidelity')
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Cover, fidelity)

        doc = pdb.get_tome_document_by_guid(tome['guid'])
        other_files = filter(lambda x: x['hash'] != file_hash, doc['files'])
        tome_file_doc = filter(lambda x: x['hash'] == file_hash, doc['files'])[0]
        tome_file_doc['fidelity'] = fidelity

        other_files.append(tome_file_doc)
        doc['files'] = other_files
        pdb.load_own_tome_document(doc)

        redirect(URL('default', 'view_tome', args=(tome['guid'])))

    return {'tome': tome, 'file_hash': file_hash, 'file_extension': file_extension, 'form': form}


def _stream_image(file_hash, extension):
    fp = pyrosetup.fileserver().get_local_file_path(file_hash)
    if fp is None:
        return
    plain_file = open(fp, 'rb')

    # \todo determine mime type and other image params
    # response.headers['Content-Type'] = 'image/jpeg'

    return response.stream(plain_file, chunk_size=20000)


@auth.requires_login()
def get_cover_image():
    image_hash = request.args[0]
    image_extension = request.args[1]
   
    return _stream_image(image_hash, image_extension)


@auth.requires_login()
def get_best_cover():
    tome_id = request.args[0]

    tome_file = pdb.get_best_relevant_cover_available(tome_id)
    if tome_file is None:
        return
    
    return _stream_image(tome_file['hash'], tome_file['file_extension'])


def _extract_image_from_content(file_hash, extension):
    """ requires a calibre installation
        returns the full path to the extracted file
    """    
    session.forget(response)

    fp = pyrosetup.fileserver().get_local_file_path(file_hash)
    if fp is None:
        raise KeyError('File not in file store')
    with open(fp, 'rb') as source_file:
        return ebook_metadata_tools.get_cover_image(source_file, extension)


def _stream_image_from_content(file_hash, extension):
    cover_target = _extract_image_from_content(file_hash, extension)
    if cover_target is not None:
        response.headers['Content-Type'] = 'image/jpeg'
        return response.stream(cover_target, chunk_size=20000)


@auth.requires_login()
def extract_cover_image_from_content():
    file_hash = request.args[0]
    file_extension = request.args[1]

    return _stream_image_from_content(file_hash, file_extension)

