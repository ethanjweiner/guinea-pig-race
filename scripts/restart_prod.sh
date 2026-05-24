#!/bin/bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-guinea-pig-race}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ "${1:-}" == "--pull" ]]; then
  echo "Pulling latest changes"
  git pull
fi

echo "Building Tailwind CSS"
poetry run tailwindcss build -i ./main_site/static/src/main.css -o ./main_site/static/dist/main.css

echo "Collecting static files"
poetry run python manage.py collectstatic --noinput

echo "Restarting ${SERVICE_NAME}"
sudo systemctl restart "$SERVICE_NAME"

echo "Service status"
sudo systemctl status "$SERVICE_NAME" --no-pager
