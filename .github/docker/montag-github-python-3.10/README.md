# montag-github-python-3.10 Docker image

## Updating the Docker image

Pick a version number for the new Docker image (e.g. `v2`), then run the
following commands:

    $ docker build --tag ghcr.io/montaggroup/montag-github-python-3.10:VERSION_NUMBER_HERE .github/docker/montag-github-python-3.10/
    $ docker login ghcr.io -u YOUR_GITHUB_USER_NAME_HERE
    $ docker push ghcr.io/montaggroup/montag-github-python-3.10:VERSION_NUMBER_HERE

Then, change the container tag in each workflow file in the .github/workflows/
directory to refer to your new version.
