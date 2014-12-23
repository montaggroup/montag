# coding: utf8
import tempfile
import subprocess
from pydb import FileType
import cStringIO


def edit_covers():
    tome_id = request.args[0]
    tome = pdb.get_tome(tome_id)
    tome_guid = tome['guid']

    tome = pdb.get_tome_document_with_local_overlay_by_guid(tome_guid, include_local_file_info=True,
                                                           include_author_detail=True)

    available_covers = []
    available_content = []

    relevant_files = filter(lambda f: f['fidelity'] >= pydb.network_params.Min_Relevant_Fidelity, tome['files'])
    relevant_local_files = filter(lambda f: f['has_local_copy'], relevant_files)

    for tome_file in relevant_local_files:
        if tome_file['file_type'] == pydb.FileType.Content:
            if tome_file['file_extension'] != 'txt':
                available_content.append(tome_file)
        elif tome_file['file_type'] == pydb.FileType.Cover:
            available_covers.append(tome_file)
        else:
            raise ValueError("Invalid value for file type")

    locally_available_covers = filter(lambda x: x['has_local_copy'], available_covers)
    
    if locally_available_covers:
        current_cover = max(locally_available_covers, key=lambda x: x['fidelity'])
    else:
        current_cover = None
        
    return {'tome': tome, 'available_covers': available_covers,
            'available_content': available_content, 'current_cover': current_cover}


def _set_cover_from_content_form():
   default_cover_fidelity = 80
   form = SQLFORM.factory(
        Field('fidelity',default=default_cover_fidelity)
        )
   return form


def set_cover_from_content():
    tome_id = request.args[0]
    content_hash = request.args[1]
    content_extension = request.args[2]

    tome = pdb.get_tome(tome_id)
    form = _set_cover_from_content_form()

    if form.process(keepvalues=True).accepted:
        fidelity = form.vars['fidelity']
        cover_contents = _extract_image_from_content(content_hash, content_extension)

        file_extension = 'jpg'
        fd_cover, path_cover = tempfile.mkstemp('.' + file_extension)
        cover_file = os.fdopen(fd_cover,'wb')
        cover_file.write(cover_contents.getvalue())
        cover_file.close()
        
        (local_file_id, file_hash, file_size) = pdb.add_file_from_local_disk(path_cover, file_extension, move_file = True)
        
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Cover, fidelity)
        redirect(URL('default', 'view_tome', args=(tome['guid'])))

    return {'tome': tome, 'content_hash': content_hash, 'content_extension': content_extension, 'form': form}


def _set_main_cover_form():
   default_cover_fidelity = 80
    # \todo use a more sensible value for fidelity
   form = SQLFORM.factory(
        Field('fidelity',default=default_cover_fidelity)
        )
   return form

def set_main_cover():
    tome_id = request.args[0]
    file_hash = request.args[1]
    file_extension = request.args[2]

    tome = pdb.get_tome(tome_id)
    form = _set_main_cover_form()
    
    file_size = pdb.get_local_file_size(file_hash)

    if form.process(keepvalues=True).accepted:
        fidelity = form.vars['fidelity']
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Cover, fidelity)

        doc = pdb.get_tome_document_by_guid(tome['guid'])
        other_files = filter( lambda x: x['hash']!=file_hash, doc['files'])
        tome_file_doc = filter( lambda x: x['hash']==file_hash, doc['files'])[0]
        tome_file_doc['fidelity'] = fidelity

        other_files.append(tome_file_doc)
        doc['files']=other_files
        pdb.load_own_tome_document(doc)

        redirect(URL('default', 'view_tome', args=(tome['guid'])))

    return {'tome': tome, 'file_hash': file_hash, 'file_extension': file_extension, 'form': form}

def _stream_image(file_hash, extension):
    fp = pdb.get_local_file_path(file_hash)
    if fp is None:
        return
    plain_file = open(fp,"rb")

    # \todo determine mime type and other image params
    # response.headers['Content-Type'] = 'image/jpeg'

    return response.stream(plain_file, chunk_size=20000)

def get_cover_image():
    image_hash = request.args[0]
    image_extension = request.args[1]
   
    return _stream_image(image_hash, image_extension)

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

    fp = pdb.get_local_file_path(file_hash)
    if fp is None:
        raise KeyError("File not in file store")
    with open(fp,"rb") as source_file:
        contents = source_file.read()

        return _get_cover_image(contents, extension)

def _get_cover_image(ebook_contents, extension):
    """ returns a cStringIO buffer with the contents of the cover file """
    # write into a temp file as to prevent ebook_convert from accessing the file store directly
    # this way we are sure that the file has the correct extension
    fd_orig, path_orig = tempfile.mkstemp('.' + extension)
    orig_file=os.fdopen(fd_orig,'wb')
    orig_file.write(ebook_contents)
    orig_file.close()
    
    fd_target, path_cover_target = tempfile.mkstemp('.jpg')
    os.close(fd_target)
    
    print "Extracting cover of {} to {}".format(path_orig, path_cover_target)
    convert_result = subprocess.call(['ebook-meta',path_orig,'--get-cover', path_cover_target])
    print "cv is", convert_result
    os.remove(path_orig)
    
    with open(path_cover_target, "rb") as coverfile:
        result = cStringIO.StringIO(coverfile.read())
    os.remove(path_cover_target)
    
    return result


def _stream_image_from_content(file_hash, extension):
    cover_target = _extract_image_from_content(file_hash, extension)

    response.headers['Content-Type'] = 'image/jpeg'

    return response.stream(cover_target, chunk_size=20000)

def extract_cover_image_from_content():
    file_hash = request.args[0]
    file_extension = request.args[1]

    return _stream_image_from_content(file_hash, file_extension)


        

    
def index(): return dict(message="hello from covers.py")
