import unittest

import pydb.comservice as comservice


class TestComserviceBuild(unittest.TestCase):
    def test_build_does_not_crash(self):
        comservice.build()


class TestComserviceLocking(unittest.TestCase):
    def setUp(self):
        self.cs = comservice.build()

    def test_when_locking_a_new_hash_it_results_in_locked(self):
        result = self.cs.lock_file_for_fetching('abc')
        self.assertEqual(result, 'locked')

    def test_when_locking_a_hash_twice_it_results_in_busy(self):
        self.cs.lock_file_for_fetching('abc')
        result = self.cs.lock_file_for_fetching('abc')
        self.assertEqual(result, 'busy')

    def test_when_locking_a_hash_that_has_been_successfully_released_it_results_in_completed(self):
        self.cs.lock_file_for_fetching('abc')
        self.cs.release_file_after_fetching('abc', True)
        result = self.cs.lock_file_for_fetching('abc')
        self.assertEqual(result, 'completed')

    def test_when_locking_a_hash_that_has_been_unsuccessfully_released_it_results_in_locked(self):
        self.cs.lock_file_for_fetching('abc')
        self.cs.release_file_after_fetching('abc', False)
        result = self.cs.lock_file_for_fetching('abc')
        self.assertEqual(result, 'locked')


if __name__ == '__main__':
    unittest.main()
