#!/bin/sh

# This MUST be the same as in `build/testing.yml`!
IMAGE_NAME=sipa_testing

# Check whether the image has been built already
docker images | grep "^$IMAGE_NAME " > /dev/null
if [ -n $? ]
then docker-compose -f build/testing.yml build
fi

# Run the tests
docker run --rm -v $(pwd):/home/sipa/sipa $IMAGE_NAME python manage.py test
