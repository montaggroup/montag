# coding=utf-8
import unittest
from pydb import montag_auth


class TestDetermineRole(unittest.TestCase):
    def setUp(self):
        self.role_config = montag_auth.RoleConfig('anon_all', 'anon_local', 'auth_all', 'auth_local')
        self._result = ""

    def given(self, is_local_session, is_user_logged_in):
        self._result = montag_auth.determine_role(self.role_config, is_local_session, is_user_logged_in)

    def expect(self, role_name):
        self.assertEqual(self._result, role_name)

    def test_non_local_and_non_logged_in_results_in_anonymous_all(self):
        self.given(is_local_session=False, is_user_logged_in=False)
        self.expect('anon_all')

    def test_non_local_and_logged_in_results_in_authenticated_all(self):
        self.given(is_local_session=False, is_user_logged_in=True)
        self.expect('auth_all')

    def test_local_and_non_logged_in_results_in_anonymous_local(self):
        self.given(is_local_session=True, is_user_logged_in=False)
        self.expect('anon_local')

    def test_local_and_logged_in_results_in_authenticated_local(self):
        self.given(is_local_session=True, is_user_logged_in=True)
        self.expect('auth_local')


class TestHasPrivilege(unittest.TestCase):
    def test_viewer_has_read_privilege(self):
        self.assertTrue(montag_auth.role_has_privilege('viewer', 'data_view'))

    def test_viewer_has_no_admin_privilege(self):
        self.assertFalse(montag_auth.role_has_privilege('viewer', 'administer'))

    def test_admin_has_admin_privilege(self):
        self.assertTrue(montag_auth.role_has_privilege('admin', 'administer'))

    def test_raises_key_error_if_role_undefined(self):
        with self.assertRaises(KeyError):
            montag_auth.role_has_privilege('pizza chef', 'administer')

    def test_empty_role_string_results_in_no_privileges(self):
        self.assertFalse(montag_auth.role_has_privilege('', 'data_read'))


if __name__ == '__main__':
    unittest.main()
