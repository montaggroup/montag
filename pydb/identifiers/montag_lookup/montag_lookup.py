# coding=utf-8
import logging

logger = logging.getLogger(__name__)


class MontagLookupByHash(object):
    def __init__(self, pydb_):
        self.pydb = pydb_

    def identify(self, file_info, file_facts):
        results = []
        hash_ = file_info['hash']
        tome_files_by_hash = self.pydb.get_tome_files_by_hash(hash_)
        for tome_file in tome_files_by_hash:
            tome_id = tome_file['tome_id']
            tome = self.pydb.get_tome(tome_id)
            tome_guid = tome['guid']

            results.append(make_result('MontagLookupByHash', tome_file['fidelity'], tome_guid))
        return results


def make_result(identifier_name, fidelity, existing_tome_guid):
    doc = {'guid': existing_tome_guid, 'file_already_added_with_correct_fidelity': True}
    return {'identifier_name': identifier_name,
            'fidelity': fidelity,
            'document': doc}