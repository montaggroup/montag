#!/bin/bash
set -o errexit

nosetests pydb/unittests $@
cd pydb/testing 
nosetests . $@