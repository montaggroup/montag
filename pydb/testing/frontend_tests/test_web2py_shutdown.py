import unittest
import httplib
import service_helpers


class TestWeb2pyShutdown(unittest.TestCase):
    def setUp(self):
        self.connection = None
        service_helpers.start_services(service_base_names=('pydbserver', 'indexserver', 'web2py'))

    def tearDown(self):
        if self.connection is not None:
            self.connection.close()
        service_helpers.stop_services()

    def test_shutdown_works_while_not_connected(self):
        service_helpers.stop_services(ignore_exceptions=False)

    def test_shutdown_works_while_client_connected(self):
        self.connection = httplib.HTTPConnection('localhost', 8000, timeout=10)
        self.connection.connect()
        self.connection.putrequest('GET', '/montag/')
        service_helpers.stop_services(ignore_exceptions=False)


if __name__ == '__main__':
    unittest.main()
