# coding=utf-8
if False:
    from ide_fake import *

import os
import sys
import Pyro4.util
from pydb import pyrosetup

web2py_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
pydb_dir = web2py_dir
for i in range(0, 4):
    pydb_dir, _ = os.path.split(pydb_dir)

if pydb_dir not in sys.path:
    sys.path.append(pydb_dir)

response.breadcrumb_bar = request.function.replace('_', ' ').title()

sys.excepthook = Pyro4.util.excepthook

pdb = pyrosetup.pydbserver()
