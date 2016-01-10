# coding=utf-8
import copy
import logging
from pydb import network_params

logger = logging.getLogger("documents")


def _prepare_fusion_sources(document, guid):
    new_fusion_sources = []
    if 'fusion_sources' in document:
        for i in document['fusion_sources']:
            i['fidelity'] = float(i['fidelity'])
            source_guid = i['source_guid']
            if source_guid > guid:
                logger.error("Document {} has a fusion source {} "
                             "which has a greater guid than the target - "
                             "this is a protocol violation, ignoring fusion source").format(guid, source_guid)
            else:
                new_fusion_sources.append(i)
    return new_fusion_sources


def prepare_tome_document(original_tome_doc, local_db):
    """ returns a new tome document with many corrections and checks applied """
    tome_doc = copy.deepcopy(original_tome_doc)
    if 'prepared' in tome_doc:
        raise ValueError(u'Tome document already prepared: {}'.format(tome_doc))
    if 'guid' not in tome_doc:
        raise ValueError(u'Tome document did not contain a guid: {}'.format(tome_doc))
    # it's not a deleted tome
    tome_guid = tome_doc['guid']
    if 'title' in tome_doc:

        tome_doc['fidelity'] = float(tome_doc['fidelity'])
        tome_doc['principal_language'] = _wrap_language(tome_doc['principal_language'])

        if not tome_doc['publication_year'] is None:
            try:
                tome_doc['publication_year'] = int(tome_doc['publication_year'])
            except ValueError:
                tome_doc['publication_year'] = None

        for i in tome_doc['tags']:
            i['tag_value'] = i['tag_value'].strip().replace("\n", "_")
            i['fidelity'] = float(i['fidelity'])

        for i in tome_doc['authors']:
            i['fidelity'] = float(i['fidelity'])

        files = {}
        for i in tome_doc['files']:
            i['fidelity'] = float(i['fidelity'])
            i['hash'] = local_db.translate_file_hash(i['hash'].lower())
            i['file_extension'] = i['file_extension'].lower()

            # deduplicate (e.g. translations)
            file_hash = i['hash']
            if file_hash in files:
                if i['fidelity'] > files[file_hash]['fidelity']:
                    files[file_hash] = i
            else:
                files[file_hash] = i

        tome_doc['files'] = files.values()

        synopses = tome_doc['synopses']
        tome_doc['synopses'] = []
        for syn in synopses:
            if syn['content'].strip():
                syn['fidelity'] = float(syn['fidelity'])
                tome_doc['synopses'].append(syn)

        tome_doc['fusion_sources'] = _prepare_fusion_sources(tome_doc, tome_guid)

    tome_doc['prepared'] = True

    return tome_doc


def prepare_author_document(original_author_doc):
    """ returns a new author document with many corrections and checks applied """
    author_doc = copy.deepcopy(original_author_doc)
    if 'prepared' in author_doc:
        raise ValueError(u'Author document already prepared: {}'.format(author_doc))
    if 'guid' not in author_doc:
        raise ValueError(u'Author document did not contain a guid: {}'.format(author_doc))

    # it's not a deleted author
    guid = author_doc['guid']
    if 'name' in author_doc:
        author_doc['fidelity'] = float(author_doc['fidelity'])
        author_doc['fusion_sources'] = _prepare_fusion_sources(author_doc, guid)

    return author_doc


def _wrap_language(lan):
    langs = {'eng': 'en',
             'spa': 'es',
             'deu': 'de',
             'por': 'pt'}

    if lan in langs:
        return langs[lan]

    return lan


def document_export_filter(items, ignore_fidelity_filter):
    return [_without_ids_and_mod_date(item) for item in items
            if abs(item['fidelity']) >= network_params.Min_Relevant_Fidelity or ignore_fidelity_filter]


def _without_ids_and_mod_date(a_dict):
    return {k: v for k, v in a_dict.iteritems() if
            k != 'id' and k != 'tome_id' and k != 'last_modification_date' and
            k != 'link_last_modification_date' and k != 'local_file_exists'}


def _list_to_dict(items, key_name):
    result = {}
    for item in items:
        key_val = item[key_name]
        result[key_val] = item
    return result


def calculate_required_edit_fidelity(merge_db_item, items_from_friends):
    required_fidelity = merge_db_item['fidelity'] + 0.1
    for friend_item in items_from_friends:
        friend_fidelity = friend_item['fidelity']
        friend_outbid_fidelity = friend_fidelity + network_params.Friend_Fidelity_Deduction * 2 + 0.1
        if friend_outbid_fidelity > required_fidelity:
            required_fidelity = friend_outbid_fidelity
    if required_fidelity > 100:
        required_fidelity = 100
    return required_fidelity


def remove_detail_tags(tome_document):
    """
    edits the tome in place
    :return: None
    """
    tome_document['tags'] = [tag for tag in tome_document['tags'] if not tag['tag_value'].startswith('<')]
