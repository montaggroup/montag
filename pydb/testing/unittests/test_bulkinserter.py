# coding=utf-8
# coding=utf-8
import unittest

import mock

import pydb.com.bulk_inserter


class TestBulkInserter(unittest.TestCase):
    def setUp(self):
        self.main_db = mock.MagicMock()
        self.friend_id = 5
        self.tome1 = mock.MagicMock()
        self.author1 = mock.MagicMock()
        self.inserter = pydb.com.bulk_inserter.BulkInserter(self.main_db, self.friend_id)

    def testEmpty_no_action(self):
        self.assertFalse(self.main_db.load_tome_documents_from_friend.called)
        self.assertFalse(self.main_db.load_author_documents_from_friend.called)

    def test_queue_tome_triggers_no_insert(self):
        self.inserter.queue_tome(self.tome1)

        self.assertFalse(self.main_db.load_tome_documents_from_friend.called)
        self.assertFalse(self.main_db.load_author_documents_from_friend.called)

    def test_insert_on_empty_triggers_no_insert(self):
        self.inserter.do_insert()
        self.assertFalse(self.main_db.load_tome_documents_from_friend.called)
        self.assertFalse(self.main_db.load_author_documents_from_friend.called)

    def test_insert_single_tome(self):
        self.inserter.queue_tome(self.tome1)
        self.inserter.do_insert()

        self.assertFalse(self.main_db.load_author_documents_from_friend.called)
        self.main_db.load_tome_documents_from_friend.assert_called_once_with(self.friend_id, [self.tome1])

    def test_insert_author_called_before_insert_tome(self):
        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_author(self.author1)
        self.inserter.do_insert()

        expected_calls = [
            mock.call.load_author_documents_from_friend(self.friend_id, [self.author1]),
            mock.call.load_tome_documents_from_friend(self.friend_id, [self.tome1])
        ]

        self.assertEquals(expected_calls, self.main_db.mock_calls)

    def test_queue_limit_max(self):
        self.inserter.set_queue_limit(2)

        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_tome(self.tome1)
        self.assertFalse(self.main_db.load_tome_documents_from_friend.called)

    def test_exceeding_queue_limit_causes_no_flush(self):
        self.inserter.set_queue_limit(2)

        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_tome(self.tome1)

        self.assertFalse(self.main_db.load_author_documents_from_friend.called)
        self.main_db.load_tome_documents_from_friend.assert_called_once_with(
            self.friend_id, [self.tome1, self.tome1, self.tome1]
        )

    def test_exceeding_queue_limit_causes_flush(self):
        self.inserter.set_queue_limit(2)

        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_tome(self.tome1)
        self.inserter.queue_tome(self.tome1)

        call_count_load_document = len(self.main_db.load_tome_documents_from_friend.mock_calls)

        # call count should not be increased as do_insert should have nothing to insert
        self.inserter.do_insert()

        call_count_load_document_after = len(self.main_db.load_tome_documents_from_friend.mock_calls)
        self.assertEquals(call_count_load_document, call_count_load_document_after)
