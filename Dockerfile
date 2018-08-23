FROM ubuntu:17.10

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
    sudo \
    nginx \
    python3-minimal \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd django && useradd -g django django && \
    echo "django ALL=(root) NOPASSWD: $(which nginx)" >> /etc/sudoers && \
    mkdir -p /var/www/static && chown django:django /var/www/static && \
    touch /tmp/nginx.pid && chown django:django /tmp/nginx.pid && \
    mkdir -p /var/log/nginx && chown django:django /var/log/nginx && \
    mkdir -p /var/lib/nginx && chown django:django /var/lib/nginx

# By copying over requirements first, we make sure that Docker will cache
# our installed requirements rather than reinstall them on every build
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

USER django

# Now copy in our code, and run it
COPY --chown=django:django . /app

# Collect static files
COPY nginx.conf /etc/nginx/nginx.conf
RUN python3 -u manage.py collectstatic --link

# Now copy in our code, and run it
COPY . /app
EXPOSE 8000
CMD sudo nginx && \
    gunicorn --config gunicorn_config.py djangodocker.wsgi
