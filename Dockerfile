FROM python:3.6-jessie

WORKDIR /app

ENV EMAIL_HOST=placeholder \
    EMAIL_PORT=25 \
    EMAIL_HOST_USER=placeholder \
    EMAIL_HOST_PASSWORD=placeholder \
    CELERY_BROKER_URL=placeholder \
    URL=placeholder \
    HOST=placeholder \
    DEBUG=0 \
    SECRET_KEY=INSECURE \
    DB_HOST=placeholder \
    DB_NAME=placeholder \
    DB_USER=placeholder \
    DB_PASSWORD=placeholder

# Install nginx, and then clean up
RUN apt-get update && apt-get install --no-install-recommends -y sudo nginx \
    && rm -rf /var/lib/apt/lists/*

# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

RUN groupadd django && useradd -g django django && usermod -aG adm django
RUN echo "django ALL=(root) NOPASSWD: $(which nginx)" >> /etc/sudoers
RUN mkdir -p /var/www/static && chown django:django /var/www/static
RUN touch /tmp/nginx.pid && chown django:django /tmp/nginx.pid
RUN mkdir -p /var/log/nginx && chown django:django /var/log/nginx
RUN mkdir -p /var/lib/nginx && chown django:django /var/lib/nginx
USER django

# Now copy in our code, and run it
COPY --chown=django:django . /app

# Collect static files
COPY nginx.conf /etc/nginx/nginx.conf
RUN python -u manage.py collectstatic

EXPOSE 8000
CMD sudo nginx && \
    gunicorn --config gunicorn_config.py djangodocker.wsgi
