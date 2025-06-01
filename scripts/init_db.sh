#!/bin/bash

echo "Migrating database"
python3 manage.py migrate
python3 manage.py seed