FROM ubuntu:22.04

RUN apt-get -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends bash git python3-pip python3.10-venv libz-dev python3-dev build-essential calibre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

LABEL org.opencontainers.image.source="https://github.com/montaggroup/montag"

