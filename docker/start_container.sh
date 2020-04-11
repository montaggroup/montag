if [ ! -d /srv/montag/metadata ]
then
	sudo mkdir -p /srv/montag/metadata
fi

# use this command to mount have all data reside in /var/lib/montag 
docker run -d -p 8000:8000 -p 8451:8451 --name montag \
  -v /srv/montag:/srv/montag \
  montag:latest

# to mount use another mount point for the bulk files (books), use the following command

#docker run -d -p 8000:8000 -p 8451:8451 --name montag \
#  -v /srv/montag/metadata:/srv/montag/metadata \
#  -v /large_volume/books:/srv/montag/books \
#  montag:latest
 
