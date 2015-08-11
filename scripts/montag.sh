#!/bin/bash

MONTAG_USER=montag
MONTAG_BASEPATH=/home/${MONTAG_USER}/montag 
SERVICES_SCRIPT=${MONTAG_BASEPATH}/montag-services.py


use_venv () {
    if [ -d ${MONTAG_BASEPATH}/venv ]
    then
        source ${MONTAG_BASEPATH}/venv/bin/activate
    fi
}

use_venv

start() {
    python ${SERVICES_SCRIPT} start
}

status() {
    python ${SERVICES_SCRIPT} status
}

stop() {
    python ${SERVICES_SCRIPT} stop
}

restart() {
    python ${SERVICES_SCRIPT} restart
}

case "$1" in
    start)
        start
    ;;
    stop)
        stop
    ;;
    restart)
        restart
    ;;
    status)
        status
    ;;
    *)
        echo "Usage ${0} (start|stop|restart|status)"
    ;;
esac

