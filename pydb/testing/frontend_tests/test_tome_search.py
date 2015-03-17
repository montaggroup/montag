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
    pydb.services.start(pydb.services.service_name('indexserver'))


def stop_services():
    pydb.services.stop_all_ignoring_exceptions()


def dump_result(res):
    for key, value in res.iteritems():
        print "{}: {}".format(key, value)


class TestTomeSearch(unittest.TestCase):
    def setUp(self):
        self.env = prepare_environment('default')
        self.request = self.env['request']
        self.response = self.env['response']
        start_services()

    def tearDown(self):
        stop_services()

    def _add_args(self, *args):
        for arg in args:
            self.request.args.append(arg)

    def _add_post_vars(self, var_dict):
        self.request.vars.update(var_dict)
        self.request.post_vars.update(var_dict)

    def test_opening_search_form_returns_a_form_element_and_view_renders(self):
        res = self.env['tomesearch']()
        self.assertIn('form', res)

        html = self.response.render('default/tomesearch.html', res)
        self.assertIn('<form ', html)

    def test_executed_search_from_returns_a_result_list_and_view_renders(self):
        self._add_post_vars({
            '_formname': 'search',
            'query': 'hello',
            'principal_language': 'en',
            'tome_type': '2'
        })
        res = self.env['tomesearch']()
        self.assertIn('tome_info', res)

        html = self.response.render('default/tomesearch.html', res)
        self.assertIn('Results for hello', html)


if __name__ == '__main__':
    unittest.main()
