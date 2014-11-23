#!/usr/bin/python2.7

from distutils.core import setup
import py2exe
from glob import glob

sql_schemas = [('db-schemas', glob('db-schemas/*'))]
data_files = []
data_files += sql_schemas

web2py_packages=[
    "SimpleXMLRPCServer",
    "htmllib",
    "HTMLParser",
    "shelve",
    "logging.config",
    "code",
    "wsgiref.headers",
    "wsgiref.util",
    "email",
    "email.mime",
    "email.mime.base"
]

setup(

    options={
        'py2exe': {
            'includes' : ['zope.interface', 'psutil'],
            'packages': ['pydb.config', 'pydb.maindb']+web2py_packages
        }
    },

    # windows =
    console=[
        {"script": "montag-pydbserver.py"},
        {"script": "pydbtool.py"},
        {"script": "montag-comserver.py"},
        {"script": "montag-comservice.py"},
        {"script": "montag-indexserver.py"},
        {"script": "montag-services.py"},
        {"script": "montag-web2py.py"}
    ],
    data_files=data_files,

    requires=['Pyro4', 'mock', 'twisted', 'whoosh', 'PySide', 'lxml', 'ijson', 'Crypto', 'psutil', 'pycryptopp',
              'bitarray', 'PyPDF2', 'PIL', 'PIL']
 )


