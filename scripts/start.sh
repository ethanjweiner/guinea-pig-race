#!/bin/bash
echo Starting NGinx
service nginx start

echo Starting Gunicorn

gunicorn race_site.wsgi:application --bind 127.0.0.1:8000