# coding=utf-8
import unittest
import logging

import pydb.pyrosetup
import pydb.testing
import service_helpers
import web2py_helpers
import config_helpers
from gluon import http

web2py_helpers.prepare_web2py()

logging.basicConfig(level=logging.WARNING)


class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.tc_folder = pydb.testing.get_clean_testcase_folder(self.id())
        service_helpers.start_services(self.tc_folder)

    def tearDown(self):
        service_helpers.stop_services()

    def test_viewer_role_can_not_access_edit_tome(self):
        # our requests are non-local, anonymous
        config_helpers.add_setting(self.tc_folder, "permissions", "role_anonymous_all", "viewer")
        self.edit_tome = web2py_helpers.build_request(self.tc_folder, 'default', 'edit_tome')

        self.edit_tome.add_args("dadasdasfasfadfs")

        try:
            self.edit_tome.execute()
        except http.HTTP as e:
            self.assertIn('Location', e.headers)
            self.assertIn('login', e.headers['Location'])
        else:
            self.assertTrue(False, "Expected http redirect")


if __name__ == '__main__':
    unittest.main()
