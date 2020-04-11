# Running montag using docker

## Using the prebuild image

`docker run -d -p 8000:8000 dsk7/montag:latest`

## Build the image yourself
run 

`./build_image.sh`

This downloads the current montag master from github and builds a docker
image from it.

## Customising storage locations

To persist books and database, use docker volume mounts.
Pass the following commands to docker run

`  -v /var/lib/montag/data:/srv/montag/data` 

This puts all metadata to /var/lib/montag/data


`  -v /large_volume/books:/srv/montag/books`

This puts all books to /var/lib/montag/books

For more examples, see `start-container.sh`.

