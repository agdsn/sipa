#!/bin/sh
cd /home/sipa/sipa

exec /usr/local/bin/uwsgi \
    --master \
    --socket 0.0.0.0:5000 \
    --wsgi-file sipa.py \
    --callable app
