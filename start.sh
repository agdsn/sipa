#!/bin/sh
cd /home/sipa/sipa

exec /usr/local/bin/uwsgi -s 0.0.0.0:5000 --wsgi-file sipa.wsgi --callable app --uid sipa  --gid sipa
