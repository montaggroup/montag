# -*- coding: utf-8 -*-
if False:
    from pydb_helpers.ide_fake import *

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

db = DAL('sqlite://storage.sqlite')

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from pydb import montag_auth
from gluon.tools import Auth, Crud, Service, PluginManager

web2py_auth = Auth(db, hmac_key=Auth.get_or_create_key())
web2py_auth.define_tables()
web2py_auth.settings.actions_disabled.append('register')
web2py_auth.settings.actions_disabled.append('request_reset_password')
web2py_auth.settings.reset_password_requires_verification = True

auth = montag_auth.MontagAuth(web2py_auth, request)

crud, service, plugins = Crud(db), Service(), PluginManager()