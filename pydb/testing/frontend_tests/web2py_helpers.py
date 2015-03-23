import os
import gluon.shell
import sys


def prepare_web2py():
    """ changes the current directory into web2py path - otherwise the environment won't work
    """
    web2py_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'web2py')
    sys.path.append(os.path.realpath(web2py_path))
    os.chdir(web2py_path)


def build_request(controller_name, function_name):
    env = _prepare_environment(controller_name)
    return Web2pyRequest(env, controller_name, function_name)


class Web2pyRequest():
    def __init__(self, environment, controller_name, function_name):
        self.env = environment
        self.request = self.env['request']
        self.response = self.env['response']
        self.controller_name = controller_name
        self.function_name = function_name
        self.result = None

    def add_args(self, *args):
        for arg in args:
            self.request.args.append(arg)

    def add_post_vars(self, var_dict):
        self.request.vars.update(var_dict)
        self.request.post_vars.update(var_dict)

    def add_get_vars(self, var_dict):
        self.request.vars.update(var_dict)
        self.request.get_vars.update(var_dict)

    def execute(self):
        self.result = self.env[self.function_name]()
        return self.result

    def dunmp_result(self):
        for key, value in self.result.iteritems():
            print "{}: {}".format(key, value)

    def render_result(self):
        if self.result is None:
            self.execute()

        self.response._view_environment.update(self.env)
        view_file = '{}/{}.html'.format(self.controller_name, self.function_name)
        html = self.response.render(view_file, self.result)
        return html


def _prepare_environment(controller_name):
    app_dir = os.path.join('applications', 'montag')
    db_dir = os.path.join(app_dir, 'databases')
    if not os.path.isdir(db_dir):  # without db dir, DAL wont work
        os.mkdir(db_dir)
    env = gluon.shell.env(app_dir, c=controller_name, dir=app_dir, import_models=True)
    execfile(os.path.join(app_dir, 'controllers', controller_name + '.py'), env)

    return env

