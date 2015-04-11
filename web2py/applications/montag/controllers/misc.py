# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *


@auth.requires_login()
def install_search_bar():
    response.headers['Content-Type'] = 'application/xml'
    return {}
