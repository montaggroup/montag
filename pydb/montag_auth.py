# coding=utf-8
from collections import namedtuple
import pydb.config

valid_roles = ['viewer', 'editor', 'admin']
valid_privileges = ['data_view', 'data_edit', 'friends_view', 'statistics_view', 'administer']

privileges_by_role = {
    'viewer': ['data_view'],
    'editor': ['data_view', 'data_edit', 'statistics_view'],
    'admin': valid_privileges
}

RoleConfig = namedtuple('RoleConfig', ['role_anonymous_all',
                                       'role_anonymous_localhost',
                                       'role_authenticated_all',
                                       'role_authenticated_localhost'])


class MontagAuth(object):
    def __init__(self, web2py_auth, request):
        self.web2py_auth = web2py_auth
        self.role_config = load_auth_config()
        self.web2py_request = request
        self.settings = web2py_auth.settings

    def logout(self):
        return self.web2py_auth.logout()

    def is_user_logged_in(self):
        return bool(self.web2py_auth.user)

    def has_privilege(self, privilege):
        if privilege not in valid_privileges:
            raise ValueError("Invalid privilege '{}' specified".format(privilege))
        role = determine_role(self.role_config,
                              is_user_logged_in=bool(self.web2py_auth.user),
                              is_local_session=self.web2py_request.is_local)
        return role_has_privilege(role, privilege)

    def _require(self, privilege):
        return self.web2py_auth.requires(lambda: self.has_privilege(privilege),
                                         requires_login=lambda: not self.has_privilege(privilege))

    def requires_data_view_permission(self):
        return self._require('data_view')

    def requires_data_edit_permission(self):
        return self._require('data_edit')

    def requires_friend_view_permission(self):
        return self._require('friends_view')

    def requires_statistics_permission(self):
        return self._require('statistics_view')

    def requires_admin_permission(self):
        return self._require('administer')

    def __call__(self, *args, **kwargs):
        return self.web2py_auth()


def determine_role(role_config, is_local_session, is_user_logged_in):
    """
    :param role_config: RoleConfig
    :param is_local_session: bool
    :param is_user_logged_in: bool
    :return:
    """

    if is_local_session:
        if is_user_logged_in:
            return role_config.role_authenticated_localhost
        else:
            return role_config.role_anonymous_localhost
    else:
        if is_user_logged_in:
            return role_config.role_authenticated_all
        else:
            return role_config.role_anonymous_all


def role_has_privilege(role, privilege):
    """
    will raise a key error if role unknown
    will accept role='' and return false
    """
    if not role:
        return False

    privileges = privileges_by_role[role]
    return privilege in privileges


def load_auth_config():
    def get_role_config(name, default_role=''):
        role = pydb.config.get_string_option('permissions', name, default_role)
        if role and role not in valid_roles:
            raise ValueError("Invalid role '{}' for configuration option '{}' in config file.".format(role, name))
        return role

    return RoleConfig(
            role_anonymous_all=get_role_config('role_anonymous_all', 'editor'),
            role_anonymous_localhost=get_role_config('role_anonymous_localhost', 'admin'),
            role_authenticated_all=get_role_config('role_authenticated_all', 'editor'),
            role_authenticated_localhost=get_role_config('role_authenticated_localhost', 'admin')
    )
