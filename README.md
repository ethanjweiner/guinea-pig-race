# The Guinea Pig Mile

Welcome to The Guinea Pig Mile. 4 laps. 1609 meters. A race so beautiful it’ll make you believe in a higher power, and so painful it’ll make you pray to one.

## Running this App

- Install dependencies (tailwind, etc.)
- Run `./tailwind.sh` and `python manage.py runserver`

## Seeding Data

- Run `python manage.py seed`

## Installing Dependencies

Add new deps by running `python -m pip install` to install in this project's `venv`.

## Deploying App

- Build Docker image: `docker buildx build --platform linux/amd64 -t ethanjweiner/guinea-pig-race:latest .`
- Run Docker image
- Run Sqlite setup, static file collection, & gunicorn + nginx startup scripts in image
- Visit at port `8000`
