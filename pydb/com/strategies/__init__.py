default_max_files_to_request = 100000

strategy_phases = {
    'connecting': 0,
    'incoming_connection': 1,
    'providing': 10,
    'providing_metadata': 11,
    'providing_files': 12,
    'requesting_metadata': 21,
    'requesting_files': 22,
    'completed': 40
}


def strategy_phase_id(strategy_phase_name_):
    return strategy_phases[strategy_phase_name_]


def strategy_phase_name(strategy_phase_id_):
    for k, v in strategy_phases.iteritems():
        if v == strategy_phase_id_:
            return k
    raise KeyError("No such item found")


def prepare_file_requester(main_db, file_requester, max_files_to_request):
    """ returns true if there are potentially more files to request """
    tome_file_hashes = main_db.get_file_hashes_to_request(max_files_to_request)
    for tome_file_hash in tome_file_hashes:
        all_source_hashes = main_db.get_all_file_hash_translation_sources(tome_file_hash)
        for source_hash in all_source_hashes:
            file_requester.queue_download_file(source_hash)

    if len(tome_file_hashes) >= max_files_to_request:
        return True
    return False


class Strategy(object):
    def __init__(self):
        self._progress_callback = None

    def set_progress_callback(self, progress_callback):
        self._progress_callback = progress_callback

    def _update_progress(self, current_phase_name, current_items_to_do, current_items_none):
        if self._progress_callback:
            self._progress_callback(strategy_phase_id(current_phase_name), current_items_to_do, current_items_none)

    def metadata_requester_reported_progress(self, number_documents_to_receive_total, number_documents_received):
        self._update_progress('requesting_metadata', number_documents_to_receive_total, number_documents_received)

    def file_requester_reported_progress(self, number_files_to_receive_total, number_files_received):
        self._update_progress('requesting_files', number_files_to_receive_total, number_files_received)

    def provider_reported_progress(self, number_documents_sent, number_files_sent):
        self._update_progress('providing', number_documents_sent, number_files_sent)
