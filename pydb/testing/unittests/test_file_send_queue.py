import unittest
import pydb.com.file_send_queue
import mock
from pydb.testing.test_data import get_book_path
from twisted.internet.task import Clock
import logging

logging.basicConfig(level=logging.DEBUG)


class TestFileSendQueue(unittest.TestCase):
    def setUp(self):
        self.session_mock = mock.MagicMock()
        self.report_progress_mock = mock.MagicMock()
        self.reactor_mock = Clock()
        self.file_server_mock = mock.MagicMock()
        self.file_server_mock.get_local_file_path.return_value = get_book_path('pg1661.epub')


        self.send_queue = pydb.com.file_send_queue.FileSendQueue(self.session_mock,
                                                                 self.file_server_mock,
                                                                 self.report_progress_mock,
                                                                 self.reactor_mock)

    def test_when_queue_is_empty_an_enqueue_call_leads_to_a_deliver_file_call(self):
        self.send_queue.enqueue('aaa')
        self.session_mock.deliver_file.assert_called_once()

    def test_when_sending_paused_on_an_empty_queue_an_enqueue_call_does_not_lead_to_a_deliver_file_call(self):
        self.send_queue.pause_sending()
        self.send_queue.enqueue('aaa')
        self.assertFalse(self.session_mock.deliver_file.called)

    def test_after_resuming_a_queue_with_a_file_in_it_deliver_file_is_called(self):
        self.send_queue.pause_sending()
        self.send_queue.enqueue('aaa')
        self.send_queue.resume_sending()
        self.assertTrue(self.session_mock.deliver_file.called)

    def test_after_resuming_a_queue_with_two_files_in_it_deliver_file_for_the_first_is_called(self):
        self.send_queue.pause_sending()
        self.send_queue.enqueue('aaa')
        self.send_queue.enqueue('baa')
        self.send_queue.resume_sending()
        self.assertTrue(self.session_mock.deliver_file.called)

        args = self.session_mock.deliver_file.call_args
        file_hash = args[0][0]
        self.assertEqual(file_hash, 'aaa')

    def test_after_resuming_an_empty_queue_nothing_happens(self):
        self.send_queue.pause_sending()
        self.send_queue.resume_sending()
        self.assertFalse(self.session_mock.deliver_file.called)

    @mock.patch('pydb.com.file_send_queue.FILE_TRANSFER_CHUNK_SIZE', 150*1000)
    def test_two_chunks_of_the_same_file_are_sent_in_correct_order(self):
        self.send_queue.enqueue('aaa')
        self.assertEqual(self.session_mock.deliver_file.call_count, 1)
        self.reactor_mock.advance(1)
        self.assertEqual(self.session_mock.deliver_file.call_count, 2)

    @mock.patch('pydb.com.file_send_queue.FILE_TRANSFER_CHUNK_SIZE', 150*1000)
    def test_after_two_chunks_of_the_same_file_are_sent_the_second_file_is_send_as_well(self):
        self.send_queue.enqueue('aaa')
        self.send_queue.enqueue('baa')
        self.reactor_mock.advance(1)
        self.reactor_mock.advance(1)

        args = self.session_mock.deliver_file.call_args
        file_hash = args[0][0]
        self.assertEqual(file_hash, 'baa')
        self.assertEqual(self.session_mock.deliver_file.call_count, 4)

if __name__ == '__main__':
    unittest.main()
