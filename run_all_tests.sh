#!/bin/bash
set -o errexit

nosetests pydb/testing/unittests $@
nosetests pydb/testing/integration_tests $@