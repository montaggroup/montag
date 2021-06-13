#!/bin/bash

mkdir -p /srv/montag/books/{filestore,import_watch}
mkdir -p /srv/montag/metadata/{db,config,logs,web2py_databases,web2py_private}

if [ ! -f /srv/montag/metadata/config/pydb.conf ]
then
  cp /opt/montag/pydb.conf.template /srv/montag/metadata/config/pydb.conf
fi

cd /opt/montag/montag
source venv/bin/activate
python montag-services.py start -P /srv/montag/metadata/logs/
trap : TERM INT
tail -f /dev/null & wait
