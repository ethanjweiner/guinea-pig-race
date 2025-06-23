#!/bin/bash

echo "Building static files"
poetry run python manage.py collectstatic --noinput