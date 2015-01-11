#!/bin/bash
set -o errexit

./run_unittests.sh
cd pydb/testing
nosetests .