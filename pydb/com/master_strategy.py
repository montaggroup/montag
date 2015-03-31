import strategies.early_requester
import strategies.late_requester
import metadata_requester
import file_requester
import background_file_inserter
import provider
import pydb.config


def construct_master_client_strategy(main_db, comservice, file_server):
    metadata_requester_to_use = metadata_requester.MetadataRequester(main_db)
    file_requester_to_use = build_file_requester(main_db, comservice)
    provider_to_use = provider.Provider(main_db, file_server)

    return strategies.late_requester.LateRequester(metadata_requester_to_use, file_requester_to_use,
                                                   provider_to_use, main_db)


def construct_master_server_strategy(main_db, comservice, file_server):
    metadata_requester_to_use = metadata_requester.MetadataRequester(main_db)
    file_requester_to_use = None
    if pydb.config.request_files_on_incoming_connection():
        file_requester_to_use = build_file_requester(main_db, comservice)
    provider_to_use = provider.Provider(main_db, file_server)
    return strategies.early_requester.EarlyRequester(metadata_requester_to_use, file_requester_to_use,
                                                     provider_to_use, main_db)


def build_file_requester(main_db, comservice):
        file_inserter = background_file_inserter.BackgroundFileInserter()
        download_queue = file_requester.DownloadQueue()
        return file_requester.FileRequester(main_db, comservice, file_inserter, download_queue)
