FROM debian:bookworm

RUN apt-get -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends python3-pip python3-virtualenv virtualenv libz-dev python3-dev build-essential calibre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

LABEL org.opencontainers.image.source="https://github.com/montaggroup/montag"

