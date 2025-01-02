from django.apps import AppConfig

import os
import sys

pydb_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)))
for i in range(2):
    pydb_dir, _ = os.path.split(pydb_dir)

if pydb_dir not in sys.path:
    sys.path.append(pydb_dir)

import pydb.config


class MontagWebuiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'montag_webui'

    def ready(self):
        pydb.config.read_config()
