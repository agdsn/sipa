#!/bin/bash

docker pull python:latest;
docker kill sipa;
docker kill build_sipa_1;
docker kill build_sipa_debug_1;
docker rm sipa;
docker rm build_sipa_1;
docker rm build_sipa_debug_1;

docker build -t sipa .;
echo "============================";
echo "IT´s ALIVE (Maybe it´s dead)";
echo "============================";
docker run --name sipa -p 5000:5000 -d sipa python sipa.py --exposed --debug;
