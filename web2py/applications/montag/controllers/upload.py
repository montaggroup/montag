# coding: utf8


def index(): return dict(message="hello from upload.py")

import tempfile
import os
from pydb import ebook_metadata_tools, FileType, TomeType


def upload_file_json():
        """
        File upload handler for the ajax form of the plugin jquery-file-upload
        Return the response in JSON required by the plugin
        """
        try:
            # Get the file from the form
            f = request.vars['files[]']

            (id, hash, size) = _insert_file(f.file, f.filename)

            res = dict(files=[ {"name": str(f.filename), "size": size}] )

            return gluon.contrib.simplejson.dumps(res, separators=(',',':'))

        except:
            return dict(message=T('Upload error'))

def _insert_file(file_stream, original_file_name):
        (_,extension_with_dot) = os.path.splitext(original_file_name)

        (handle, file_path)=tempfile.mkstemp(suffix=extension_with_dot)

        file=os.fdopen(handle, "w")
        file.write(file_stream.read())
        file.close()

        (id, hash, size)=db.add_file_from_local_disk(file_path, extension_with_dot[1:], move_file = True)

        return id, hash,size


def _create_upload_form():
    form = FORM(TABLE(
           TR(TD('Upload File:', INPUT(_type='file',
                                       _name='new_tome_file',
                                       requires=IS_NOT_EMPTY()))),
           TR(TD(INPUT(_type='submit',_value='Submit')))
       ))
    return form

def _title_suggestion(filename):
    (title_suggestion,_) = os.path.splitext(filename)
    if isinstance(title_suggestion, str):
        title_suggestion = title_suggestion.decode('utf-8')
    title_suggestion = title_suggestion.replace("_"," ").replace("."," ")
    return title_suggestion

def upload_file():
    form = _create_upload_form()

    if form.accepts(request.vars):
        f = request.vars.new_tome_file

        _, extension_with_dot = os.path.splitext(f.filename)
        extension = extension_with_dot[1:]

        metadata=ebook_metadata_tools.extract_metadata(f.file, extension)
        if not 'title' in metadata:
            metadata['title'] = _title_suggestion(f.filename)

        (id, hash, size) =  _insert_file(f.file, f.filename)
        session.metadata = metadata
        redirect(URL('add_tome_from_file', args=(hash, extension, size )))
    elif form.errors:
        response.flash = 'form has errors'
    return dict(form=form)

def upload_file_to_tome():
    tome_guid = request.args[0]
    form = _create_upload_form()

    tome = db.get_tome_by_guid(tome_guid)
    if tome is None:
        response.flash("Tome not found")
        return dict(form=form, tome=None)

    if form.accepts(request.vars):
        f = request.vars.new_tome_file
        
        _, extension_with_dot = os.path.splitext(f.filename)
        extension = extension_with_dot[1:]

        fidelity = 60
        (id, file_hash, size) =  _insert_file(f.file, f.filename)
        db.link_tome_to_file(tome['id'], file_hash, size, extension, FileType.Content, fidelity)
        redirect(URL('default', 'view_tome', args=(tome_guid)))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form, tome=tome)


class author_validator:
    def __init__(self, format="a", error_message="b"):
        pass

    def __call__(self, field_value):
        authors=set()
        authors_list=[]
        
        field_value=field_value.decode('utf-8')
        for line in field_value.split("\n"):
            author_name = line.strip()
            if author_name:
                if author_name in authors:
                    return None,"Duplicate author names entered: {}".format(author_name)
                authors.add(author_name)
                authors_list.append(author_name)

        if not authors:
            return None,"Empty author field"
        return authors_list, None

    def formatter(self, value):
        authors = value
        return "\n".join([author['name'].encode('utf-8') for author in authors])


def _add_tome_from_file_form(metadata):
    print "Metadata is",metadata
    def from_dict(the_dict, key, default_value=""):
        if not key in the_dict:
            return default_value
        else:
            return the_dict[key]

    form = SQLFORM.factory(
        Field('title',requires=IS_NOT_EMPTY(), default=from_dict(metadata,'title').encode('utf-8') ),
        Field('subtitle'),
        Field('principal_language',default=from_dict(metadata,'principal_language','en').encode('utf-8')),
        Field('publication_year', default=str(from_dict(metadata,'publication_year','')).encode('utf-8')),
        Field('tome_type', default=TomeType.Fiction , widget=SQLFORM.widgets.radio.widget,
              requires=IS_IN_SET({TomeType.Fiction:'fiction',TomeType.NonFiction:'non-fiction'})),
        Field('authors','text', requires=author_validator(), default= [ {'name': n} for n in metadata['author_names']]),
        Field('fidelity', default=str(60.0).encode('utf-8'))
        )
    return form


def add_tome_from_file():
    file_hash=request.args[0]
    file_extension=request.args[1]
    file_size=request.args[2]
    author_ids = []

    form=_add_tome_from_file_form(session.metadata)

    if form.process(keepvalues=True, dbio=False).accepted:
        fidelity = form.vars['fidelity'].decode('utf-8')
        author_ids = db.find_or_create_authors(form.vars['authors'],fidelity)
        tome_id = db.find_or_create_tome(form.vars['title'].decode('utf-8'),form.vars['principal_language'].decode('utf-8'), author_ids, form.vars['subtitle'].decode('utf-8'),
                                         form.vars['tome_type'], fidelity, publication_year=form.vars['publication_year'])
        tome = db.get_tome(tome_id)
        db.link_tome_to_file(tome_id,file_hash,file_size,file_extension,FileType.Content,fidelity)
        response.flash = 'Successfully created tome, please edit details now'
        redirect(URL(f='edit_tome',c='default', args=(tome['guid'])))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form,author_ids=author_ids)

def _upload_cover_form():
    
    form = FORM(TABLE(
           TR(TD('Upload File:'), TD(INPUT(_type='file',
                                       _name='new_tome_cover',
                                       requires=IS_NOT_EMPTY()))),
           TR(TD('Fidelity:'), TD(INPUT(   _type='text',
                                       value=str(75.0).encode('utf-8'),
                                       _name='fidelity',
                                       requires=IS_NOT_EMPTY()))),
           TR(TD(INPUT(_type='submit',_value='Submit')))
       ))

    return form


def upload_cover():
    tome_id = request.args[0]
    tome = db.get_tome(tome_id)

    form = _upload_cover_form()

    if form.process(keepvalues=True, dbio=False).accepted:
        fidelity = form.vars['fidelity'].decode('utf-8')

        f = request.vars.new_tome_cover
        (_, extension_with_dot)=os.path.splitext(f.filename)
        file_extension = extension_with_dot[1:]

        (id, file_hash, file_size) =  _insert_file(f.file, f.filename)
        db.link_tome_to_file(tome_id, file_hash, file_size, file_extension, FileType.Cover, fidelity)
        response.flash = 'Successfully uploaded cover'
        redirect(URL(f='view_tome',c='default', args=(tome['guid'])))
    elif form.errors:
        response.flash = 'form has errors'

    return dict(form=form,tome = tome)
