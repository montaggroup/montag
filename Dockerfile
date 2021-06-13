FROM ubuntu:bionic
MAINTAINER dsk7

# Base setup
RUN apt-get -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends python-pip python-virtualenv virtualenv libz-dev python-dev build-essential calibre && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY requirements.txt /opt/montag/montag/

SHELL ["/bin/bash", "-c"] 
RUN cd /opt/montag/montag && \
    virtualenv venv && \
    source venv/bin/activate && \
    pip install -r requirements.txt && \
    ln -s /srv/montag/books/filestore . && \
    ln -s /srv/montag/metadata/db . && \
    ln -s /srv/montag/metadata/config/pydb.conf . && \
    mkdir -p ./web2py/applications/montag && \
    ln -s /srv/montag/metadata/web2py_databases ./web2py/applications/montag/databases

COPY . /opt/montag/montag
COPY docker/scripts/entrypoint.sh docker/config/pydb.conf.template /opt/montag/

# Store web2py auth in /srv/docker volume
RUN cd /opt/montag/montag && \
	rm -rf ./web2py/applications/montag/private && \
    ln -s /srv/montag/metadata/web2py_private ./web2py/applications/montag/private

CMD ["bash", "/opt/montag/entrypoint.sh"]
    
EXPOSE 8000/tcp
EXPOSE 8451/tcp
VOLUME [ "/srv/montag/"]
