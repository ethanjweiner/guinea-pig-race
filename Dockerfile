FROM nginx:latest

# Define build arguments
ARG PRODUCTION=true
ARG ALLOWED_HOSTS=*

# Set environment variables from build args
ENV PRODUCTION=${PRODUCTION}
ENV ALLOWED_HOSTS=${ALLOWED_HOSTS}

RUN apt-get update && \
    apt-get install -y --no-install-recommends 

RUN apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-poetry \
    python3-venv \
    libpcre3 \
    libpcre3-dev \
    build-essential \
    python3-dev \
    sqlite3


RUN mkdir /app 
WORKDIR /app

COPY main_site /app/main_site
COPY race_site /app/race_site
COPY pyproject.toml /app/pyproject.toml
COPY manage.py /app/manage.py
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN poetry config virtualenvs.create false
RUN poetry install
RUN touch db.sqlite3

# Create static files directory
RUN mkdir -p /var/static && chown -R www-data:www-data /var/static

# Configure Nginx
COPY nginx-app.conf /app/nginx-app.conf
RUN ln -s /app/nginx-app.conf /etc/nginx/conf.d/
RUN mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.ORIGINAL

# Copy scripts
COPY scripts/start.sh /app/start.sh
COPY scripts/init_db.sh /app/init_db.sh
COPY scripts/build_static.sh /app/build_static.sh
RUN chmod +x /app/start.sh /app/init_db.sh /app/build_static.sh

RUN ./init_db.sh
RUN ./build_static.sh

# Start Gunicorn and Nginx 
EXPOSE 8000 
CMD ["./start.sh"]
