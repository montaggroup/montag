import unittest
import pydb.filedownloadmonitor as filedownloadmonitor


class test_calculate_delete_all(unittest.TestCase):
    def setUp(self):
        self.monitor = filedownloadmonitor.FileDownloadMonitor()

    def test_lock_file(self):
        l = self.monitor.try_lock('aaa')
        self.assertTrue(l)

    def test_lock_file_twice(self):
        l = self.monitor.try_lock('aaa')
        self.assertTrue(l)

        l = self.monitor.try_lock('aaa')
        self.assertFalse(l)

    def test_lock_after_unlock_file(self):
        l = self.monitor.try_lock('aaa')
        self.assertTrue(l)
        self.monitor.unlock('aaa')

        l = self.monitor.try_lock('aaa')
        self.assertTrue(l)

    def test_invalid_unlock_exception(self):
        self.assertRaises(KeyError, self.monitor.unlock, 'aaa')

    def test_set_completed(self):
        self.monitor.try_lock('aaa')
        self.monitor.set_completed('aaa')
        self.monitor.unlock('aaa')

    def test_set_completed_with_lock_missing(self):
        self.assertRaises(KeyError, self.monitor.set_completed, 'aaa')

    def test_try_lock_on_completed(self):
        self.monitor.try_lock('aaa')
        self.monitor.set_completed('aaa')
        self.monitor.unlock('aaa')

        self.assertIsNone(self.monitor.try_lock('aaa'))


if __name__ == '__main__':
    unittest.main()

