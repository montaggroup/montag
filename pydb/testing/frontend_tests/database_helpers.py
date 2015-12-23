# coding=utf-8
from pydb.testing import test_data
from pydb import FileType
import pydb.pyrosetup


def add_sample_author(db, name='an author'):
    author_id = db.add_author(name)
    return db.get_author(author_id)


def add_sample_tome(db, author_id, upload_a_file=False, tag_values=None):
    """

    :param tag_values: if not none, iterable of tag values to add
    """
    all_tag_values = ['one tag', 'two tag']
    if tag_values:
        all_tag_values += tag_values

    tome_id = db.add_tome(title='it is also on file!', principal_language='en', author_ids=[author_id],
                                tags_values=all_tag_values)
    tome = db.get_tome(tome_id)

    if upload_a_file:
        file_path = test_data.get_book_path('pg1661.epub')
        (file_id, file_hash, size) = pydb.pyrosetup.fileserver().add_file_from_local_disk(file_path, 'epub',
                                                                                          move_file=False)
        db.link_tome_to_file(tome_id, file_hash, size, file_extension='epub', file_type=FileType.Content,
                                   fidelity=80)
    return tome

