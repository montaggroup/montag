if False:
    from pydb_helpers.ide_fake import *

from pydb import importerdb

# @todo make nice naming: bulk import vs import overview vs bulk file import
# @todo it also would be nice to see whether (and how many) files are still waiting in the import watch folder
# @todo clear empty directories from import watch earlier so filesystem viewers can see that something's happening
@auth.requires_data_edit_permission()
def import_overview():
    file_counts = {}
    for state in importerdb.states:
        files = pdb.get_import_file_count_by_state(state)
        file_counts[state] = files

    return {
        'file_counts': file_counts
    }


@auth.requires_data_edit_permission()
def pending_files():
    items = pdb.get_import_pending_files()
    return {
        'items': items
    }


@auth.requires_data_edit_permission()
def identified_files():
    items = pdb.get_import_rececently_identified_files()
    return {
        'items': items
    }


@auth.requires_data_edit_permission()
def file_info():
    file_hash = request.args[0]

    pydb.assert_hash(file_hash)

    file_info = pdb.get_import_file_state(file_hash)
    facts = None
    identifier_results = None

    if file_info:
        facts = pdb.get_import_file_facts(file_hash)
        identifier_results = pdb.get_import_identifer_results(file_hash)


    return {
        'file_hash': file_hash,
        'file_info': file_info,
        'file_facts': facts,
        'identifier_results': identifier_results
    }
