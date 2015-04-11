# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *

import tempfile

from pydb import ebook_metadata_tools, FileType, TomeType
import pydb.pyrosetup


DEFAULT_ADD_FIDELITY = 60.0


def _insert_file(file_stream, original_file_name):
    (_, extension_with_dot) = os.path.splitext(original_file_name)

    (handle, file_path) = tempfile.mkstemp(suffix=extension_with_dot)

    with os.fdopen(handle, "wb") as f:
        f.write(file_stream.read())

    file_server = pydb.pyrosetup.fileserver()
    (file_id, file_hash, file_size) = file_server.add_file_from_local_disk(file_path, extension_with_dot[1:],
                                                                           move_file=True)

    return file_id, file_hash, file_size


def _create_upload_form():
    form = FORM(TABLE(TR(TD(DIV(DIV('Drop File Here'), _class='dz-message'))),
                      TR(TD(' -- or --')),
                      TR(TD(INPUT(_type='file', _name='file', requires=IS_NOT_EMPTY()))),
                      TR(TD(INPUT(_type='submit', _value='Submit'))),
                      _class='upload_file'),
                _class='dropzone', _id='dropzoneForm')

    return form


def _title_suggestion(filename):
    (title_suggestion, _) = os.path.splitext(filename)
    if isinstance(title_suggestion, str):
        title_suggestion = title_suggestion.decode('utf-8')
    title_suggestion = title_suggestion.replace('_', ' ').replace('.', ' ')
    return title_suggestion


@auth.requires_login()
def upload_file():
    response.enable_dropzone = True
    response.title = "Add Tome - Montag"
    form = _create_upload_form()

    if form.accepts(request.vars):
        f = request.vars.file
        is_dropzone = False
        
        if isinstance(f, list):  # dropzone uploads result in lists
            f = f[1]
            is_dropzone = True
        
        _, extension_with_dot = os.path.splitext(f.filename)
        extension = extension_with_dot[1:]

        metadata = ebook_metadata_tools.extract_metadata(f.file, extension)
        if 'title' not in metadata:
            metadata['title'] = _title_suggestion(f.filename)
        session.metadata = metadata

        f.file.seek(0)    
        (_, file_hash, size) = _insert_file(f.file, f.filename)

        target_url = URL('add_tome_from_file', args=(file_hash, extension, size))
        if is_dropzone:
            return target_url
        else:
            redirect(target_url)
         
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)


@auth.requires_login()
def upload_file_to_tome():
    tome_guid = request.args[0]

    response.enable_dropzone = True
    form = _create_upload_form()

    tome = pdb.get_tome_by_guid(tome_guid)
    if tome is None:
        response.title = u"Upload File - Montag"
        response.flash = 'Tome not found'
        return dict(form=form, tome=None)

    title_text = pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"Upload File to {} - Montag".format(title_text)

    if form.accepts(request.vars):
        f = request.vars.file
        is_dropzone = False
        
        if isinstance(f, list):  # dropzone uploads result in lists
            f = f[1]
            is_dropzone = True
        
        _, extension_with_dot = os.path.splitext(f.filename)
        extension = extension_with_dot[1:]

        fidelity = DEFAULT_ADD_FIDELITY
        (_, file_hash, size) = _insert_file(f.file, f.filename)

        pdb.link_tome_to_file(tome['id'], file_hash, size, extension, FileType.Content, fidelity)
        target_url = URL('default', 'view_tome', args=tome_guid)
        if is_dropzone:
            return target_url
        else:
            redirect(target_url)

    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome)


def _add_tome_from_file_form(metadata):
    def from_dict(the_dict, key, default_value=''):
        if key not in the_dict:
            return default_value
        else:
            return the_dict[key]

    form = SQLFORM.factory(Field('title', requires=IS_NOT_EMPTY(), default=db_str_to_form(from_dict(metadata, 'title')),
                                 comment=TOOLTIP('Please enter the title of the book like it is written on the cover.')
                                 ),
                           Field('subtitle'),
                           Field('edition'),
                           Field('principal_language',
                                 default=db_str_to_form(from_dict(metadata, 'principal_language', 'en')),
                                 comment=TOOLTIP('Please use two letter ISO 639-1 codes (e.g. en for English).')),
                           Field('publication_year',
                                 default=db_str_to_form(from_dict(metadata, 'publication_year', ''))),
                           Field('tome_type', default=TomeType.Fiction, widget=SQLFORM.widgets.radio.widget,
                                 requires=IS_IN_SET({TomeType.Fiction: 'fiction', TomeType.NonFiction: 'non-fiction'})),
                           Field('authors', 'text', requires=AuthorValidator(),
                                 default=[{'name': n} for n in metadata['author_names']]),
                           Field('fidelity', requires=FidelityValidator(), default=DEFAULT_ADD_FIDELITY),
                           submit_button='Add')
    return form


@auth.requires_login()
def add_tome_from_file():
    file_hash = request.args[0]
    file_extension = request.args[1]
    file_size = request.args[2]
    response.title = "Add Tome - Montag"

    author_ids = []

    if 'metadata' not in session:
        return create_error_page('It seems that the session broke somehow - do you have a cookie blocker?')

    form = _add_tome_from_file_form(session.metadata)

    if form.process(keepvalues=True, dbio=False).accepted:
        fidelity = read_form_field(form, 'fidelity')
        authors = read_form_field(form, 'authors')
        author_ids = pdb.find_or_create_authors(authors, fidelity)
        tome_id = pdb.find_or_create_tome(read_form_field(form, 'title'), 
                                          read_form_field(form, 'principal_language'), 
                                          author_ids, 
                                          read_form_field(form, 'subtitle'),
                                          read_form_field(form, 'tome_type'), 
                                          fidelity, 
                                          edition=read_form_field(form, 'edition'), 
                                          publication_year=read_form_field(form, 'publication_year'))

        tome = pdb.get_tome(tome_id)
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Content, fidelity)
        response.flash = 'Tome successfully added.'
        redirect(URL(f='view_tome', c='default', args=(tome['guid'])))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, author_ids=author_ids)


def _upload_cover_form():
    form = FORM(TABLE(TR(TD(DIV(DIV('Drop File Here'), _class='dz-message'))),
                      TR(TD(' -- or --')),
                      TR(TD(INPUT(_type='file',
                                  _name='file',
                                  requires=IS_NOT_EMPTY()))),
                      TR(
                          TD(INPUT(_type='submit',
                                   _value='Submit'))),
                      _class='upload_file'),
                _class='dropzone', _id='dropzoneForm')

    return form


@auth.requires_login()
def upload_cover():
    tome_id = request.args[0]
    tome = pdb.get_tome(tome_id)
    if tome is None:
        response.flash = 'Tome not found'
        return dict(form=None, tome=None)

    title_text = pydb.title.coalesce_title(tome['title'], tome['subtitle'])
    response.title = u"Upload Cover for {} - Montag".format(title_text)
    response.enable_dropzone = True

    form = _upload_cover_form()

    if form.process(keepvalues=True, dbio=False).accepted:
        f = request.vars.file
        is_dropzone = False

        if isinstance(f, list):  # dropzone uploads result in lists
            f = f[1]
            is_dropzone = True

        (_, extension_with_dot) = os.path.splitext(f.filename)
        file_extension = extension_with_dot[1:]

        (file_id, file_hash, file_size) = _insert_file(f.file, f.filename)
        pdb.link_tome_to_file(tome_id, file_hash, file_size, file_extension,
                              FileType.Cover, fidelity=DEFAULT_ADD_FIDELITY)
        response.flash = 'Successfully uploaded cover'

        target_url = URL(f='view_tome', c='default', args=(tome['guid']))

        if is_dropzone:
            return target_url
        else:
            redirect(target_url)

    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome)
