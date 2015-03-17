import sys
import os

web2py_path = os.path.join('..', '..', '..', 'web2py')
sys.path.append(os.path.realpath(web2py_path))

# web2py likes to run with current dir = web2py path
os.chdir(web2py_path)

import unittest
import gluon.globals
import gluon.shell
import pydb.services


def prepare_environment(controller_name):
    app_dir = os.path.join('applications', 'montag')
    env = gluon.shell.env(app_dir, c='default', dir=app_dir, import_models=True)
    execfile(os.path.join(app_dir, 'controllers', controller_name + '.py'), env)
    return env


def start_services():
    pydb.services.start(pydb.services.service_name('pydbserver'))


def stop_services():
    pydb.services.stop_all_ignoring_exceptions()


def dump_result(res):
    for key, value in res.iteritems():
        print "{}: {}".format(key, value)


class TestTomeSearch(unittest.TestCase):
    def setUp(self):
        self.env = prepare_environment('default')
        self.request = gluon.globals.Request({})
        start_services()

    def tearDown(self):
        stop_services()

    def test_opening_search_form_returns_a_form_element(self):
        res = self.env['tomesearch']()
        self.assertIn('form', res)


if __name__ == '__main__':
    unittest.main()
