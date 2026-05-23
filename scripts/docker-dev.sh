#!/bin/bash
set -e

python manage.py migrate

if [ "${SEED_DATABASE:-false}" = "true" ]; then
    python manage.py seed
fi

tailwindcss -i ./main_site/static/src/main.css -o ./main_site/static/dist/main.css --watch=always &
TAILWIND_PID=$!

cleanup() {
    kill "$TAILWIND_PID" 2>/dev/null || true
}
trap cleanup EXIT

python manage.py runserver 0.0.0.0:8000
