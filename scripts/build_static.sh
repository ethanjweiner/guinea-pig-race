#!/bin/bash

echo "Building static files"
python3 manage.py collectstatic --noinput