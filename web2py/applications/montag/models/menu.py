# -*- coding: utf-8 -*-
if False:
    from pydb_helpers.ide_fake import *

import pydb.config

response.title = ' '.join(word.capitalize() for word in request.application.split('_'))
response.subtitle = T('customize me!')

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Your Name <you@example.com>'
response.meta.description = 'a cool new app'
response.meta.keywords = 'web2py, python, framework'
response.meta.generator = 'Web2py Web Framework'
response.meta.copyright = 'Copyright 2014'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################


response.menu = [
]

if auth.has_privilege('data_view'):
    response.menu += [
        (T('Search'), False, URL('default', 'index'), []),
        (T('Timeline'), False, URL('default', 'timeline'), [])
    ]

if auth.has_privilege('data_edit'):
    response.menu.append((T('Add Tome'), False, URL('upload', 'upload_file'), []))

if auth.has_privilege('friends_view'):
    response.menu.append((T('Friends'), False, URL('friends', 'list_friends'), []))

if auth.has_privilege('friends_view') or auth.has_privilege('statistics_view') or auth.has_privilege('data_view'):
    response.menu.append((T('More...'), False, URL('default', 'more_actions'), []))

if pydb.config.enable_web_auth() and auth.is_user_logged_in():
    response.menu.append((T('Logout'), False, URL('default', 'user', args='logout'), []))