# Running montag using docker

## Using the prebuild image

`docker run -d -p 8000:8000 dsk7/montag:latest`

## Build the image yourself
run 

`./build.sh`

This downloads the current montag master from github and builds a docker
image from it.

## Customising storage locations

To persist books and database, use docker volume mounts.
Pass the following commands to docker run

`  -v /var/lib/montag/metadata:/srv/montag/metadata` 

This puts all metadata to /var/lib/montag/metadata


`  -v /large_volume/books:/srv/montag/books`

This puts all books to /large_volume/books into the subdirectory `filestore`.

For more examples, see `start-container.sh`.

