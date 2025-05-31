FROM python:3.10
RUN mkdir /app 
WORKDIR /app
COPY main_site /app/main_site
COPY race_site /app/race_site
COPY pyproject.toml /app/pyproject.toml
COPY manage.py /app/manage.py
ENV PYTHONPATH=${PYTHONPATH}:${PWD}
RUN apt-get update && apt-get install -y \
    sqlite3
RUN pip3 install poetry

RUN poetry config virtualenvs.create false
RUN poetry install
RUN touch db.sqlite3
RUN python manage.py migrate
RUN python manage.py seed

CMD ["gunicorn", "race_site.wsgi:application", "--bind", "0.0.0.0:8000"]