#!/bin/sh
set -o errexit

pytest pydb/testing/integration_tests
