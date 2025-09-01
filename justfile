#!/usr/bin/env just
# To install `just`, see
# https://github.com/casey/just#packages

drc := "docker compose"
test_doc := "build/testing/docker-compose.yml"


setup:
    cp example/.env .env
    @echo "Creating certificat for test environment!"
    openssl req -x509 -nodes -days 3650 -newkey rsa:4096 -keyout example/priv.key -out example/cert.crt -subj /CN=AGDSN_Test
    cat example/priv.key example/cert.crt > example/server.pem

start environment:
    @echo "Starting {{environment}} environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml up -d

stop environment:
    @echo "Stopping {{environment}} environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml down

logs:
    docker logs sipa-dev

tests:
    {{ drc }} -f {{ test_doc }} up -d
    {{ drc }} -f {{ test_doc }}  run --rm sipa_testing pytest -v

test test_to_run:
    {{ drc }} -f {{ test_doc }} up -d
    {{ drc }} -f {{ test_doc }}  run --rm sipa_testing nosetests -v {{ test_to_run }}

rebuild environment:
    @echo "Rebuilding environment!"
    {{ drc }} -f build/{{environment}}/docker-compose.yml --force-recreate --no-deps up


set backend:
    #!/usr/bin/env bash
    if [[ {{ backend }} == "sample" ]]; then \
        sed -i "s|^\(SIPA_BACKEND=\).*|\1sample|" .env; \
    elif [[ {{ backend }} == "pycroft" ]]; then
        sed -i 's|^\(SIPA_BACKEND=\).*|\1pycroft|' .env; \
    else
        echo "No vaild backend given: {{ backend }} must be sipa or pycroft!";
    fi

show-backend:
    #!/usr/bin/env bash
    echo "Backend: $(sed 's|SIPA_BACKEND=||; s|#.*||' .env)"

