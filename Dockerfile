FROM ubuntu:bionic
MAINTAINER dsk7

# Base setup
RUN apt-get -y update && \
    apt-get install -q -y --no-install-recommends git python-pip python-virtualenv virtualenv libz-dev python-dev build-essential joe && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements.txt /opt/montag/montag/

SHELL ["/bin/bash", "-c"] 
RUN cd /opt/montag/montag && \
    virtualenv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt && \
    ln -s /srv/montag/books/file_store . && \
    ln -s /srv/montag/metadata/db . && \
    ln -s /srv/montag/metadata/config/pydb.conf .

COPY . /opt/montag/montag
COPY docker/scripts/entrypoint.sh docker/config/pydb.conf.template /opt/montag/
    
CMD ["bash", "/opt/montag/entrypoint.sh"]
    
EXPOSE 8000/tcp
EXPOSE 8451/tcp
VOLUME [ "/srv/montag/"]
