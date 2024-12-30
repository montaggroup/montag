import pydb.com.strategies.early_requester
import pydb.com.strategies.late_requester
import pydb.com.metadata_requester
import pydb.com.file_requester
import pydb.com.background_file_inserter
import pydb.com.provider
import pydb.config


def construct_master_client_strategy(main_db, comservice, file_server):
    metadata_requester_to_use = pydb.com.metadata_requester.MetadataRequester(main_db)
    file_requester_to_use = build_file_requester(main_db, comservice)
    provider_to_use = pydb.com.provider.Provider(main_db, file_server)

    return pydb.com.strategies.late_requester.LateRequester(metadata_requester_to_use, file_requester_to_use,
                                                   provider_to_use, main_db)


def construct_master_server_strategy(main_db, comservice, file_server):
    metadata_requester_to_use = pydb.com.metadata_requester.MetadataRequester(main_db)
    file_requester_to_use = None
    if pydb.config.request_files_on_incoming_connection():
        file_requester_to_use = build_file_requester(main_db, comservice)
    provider_to_use = pydb.com.provider.Provider(main_db, file_server)
    return pydb.com.strategies.early_requester.EarlyRequester(metadata_requester_to_use, file_requester_to_use,
                                                     provider_to_use, main_db)


def build_file_requester(main_db, comservice):
        file_inserter = pydb.com.background_file_inserter.BackgroundFileInserter()
        download_queue = pydb.com.file_requester.DownloadQueue()
        return pydb.com.file_requester.FileRequester(main_db, comservice, file_inserter, download_queue)
