# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *

@auth.requires_login()
def index(): return dict(message="hello from misc.py")


@auth.requires_login()
def install_search_bar():
    response.headers['Content-Type']='application/xml'
    return {}
