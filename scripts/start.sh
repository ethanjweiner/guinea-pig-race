#!/bin/bash
echo Starting Gunicorn
pkill gunicorn
poetry run gunicorn race_site.wsgi:application --bind 127.0.0.1:8000 > /dev/null 2>&1 &