# coding: utf8
# try something like

@auth.requires_login()
def index(): return dict(message="hello from misc.py")


@auth.requires_login()
def install_search_bar():
    response.headers['Content-Type']='application/xml'
    return {}
