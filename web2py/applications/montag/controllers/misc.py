# coding: utf8
if False:
    from pydb_helpers.ide_fake import *


@auth.requires_data_view_permission()
def install_search_bar():
    response.headers['Content-Type'] = 'application/xml'
    return {}
