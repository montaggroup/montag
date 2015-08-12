#!/bin/bash

MONTAG_USER=montag
MONTAG_BASEPATH=/home/${MONTAG_USER}/montag
MONTAG_RUNSCRIPT=${MONTAG_BASEPATH}/scripts/montag.sh

su - ${MONTAG_USER} -c "${MONTAG_RUNSCRIPT} $1"
