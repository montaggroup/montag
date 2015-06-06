import unittest
import sys
import os

sys.path.append(os.getcwd())

import pydb.com.server
from pydb.testing.test_data import get_book_path
import logging
import mock

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_provider")


class TestProvider(unittest.TestCase):
    def setUp(self):
        pass

    def test_disconnect_detection_during_file_providing_works(self):
        session_friend_id = 4
        hash_of_file_to_request = '1234'
        job_id = 11

        main_db_mock = mock.MagicMock()
        main_db_mock.get_friend_last_query_dates.return_value = (0, 0)

        com_service_mock = mock.MagicMock()
        com_service_mock.register_job.return_value = job_id

        file_server_mock = mock.MagicMock()
        file_server_mock.get_local_file_path.return_value = get_book_path('pg1661.epub')

        session_mock = mock.MagicMock()

        session_controller = pydb.com.server.SessionController(main_db_mock, com_service_mock, file_server_mock)
        session_controller.set_lower_layer(session_mock)
        session_controller.session_established(session_friend_id)
        com_service_mock.register_job.assert_called_once_with('fetch_updates', session_friend_id)

        metadata_requester = session_controller._communication_strategy._metadata_requester
        metadata_requester.command_update_modification_date_received(0, 0)

        provider = session_controller._communication_strategy._provider
        self.assertIsNotNone(provider.lower_layer)  # check that the provider has been activated

        provider.command_request_file_received(hash_of_file_to_request)
        provider.session_lost('Disconnect (Test)')

        com_service_mock.unregister_job.assert_called_once_with(job_id)


if __name__ == "__main__":
    unittest.main()
