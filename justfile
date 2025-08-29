#!/usr/bin/env just
# To install `just`, see
# https://github.com/casey/just#packages

drc:= "docker compose"



setup test-env:
    @echo "Creating certificat for test environment!"
    docker run --rm -t cert_gen -v $(pwd)/example:/data build/testing-setup
    @echo "Building docker images"
    {{ drc }} -f build/testing-setup/docker-compose.yml build

start environment:
    @echo "Starting {{environment}} environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml up -d

stop environment:
    @echo "Stopping {{environment}} environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml down

logs:
    docker logs sipa-dev

tests:
    {{ drc }} -f build/testing/docker-compose.yml up -d
    {{ drc }} -f build/testing/docker-compose.yml run --rm sipa_testing pytest -v

rebuild environment:
    @echo "Rebuilding environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml --force-recreate --no-deps up
