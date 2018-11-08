FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

COPY ocd_backend/requirements.txt /opt/ori/ocd_backend/requirements.txt

# Install system requirements
# Second line are used for image creation and uninstalled afterwards to reduce
# layer size. Third and fourth lines are lib dependencies and fifth line are
# package dependencies
RUN apk add --update \
  build-base git tzdata \
  libxml2-dev libxslt-dev poppler-dev jpeg-dev \
  inotify-tools libmagic \
  && pip install --upgrade pip \
  && pip install cython \
  && pip install --no-cache-dir -r /opt/ori/ocd_backend/requirements.txt \
  && pip uninstall -y cython \
  && cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

# Setup Celery
# Create static data folder shared with the frontend
# Trick to redirect logs to process 1 when running multiple processes
RUN adduser -D -H celery \
  && mkdir -p /var/run/celery /opt/ori/data/static /opt/ori/data/cache /opt/ori/log \
  && ln -sf /proc/1/fd/1 /opt/ori/log/stdout

# Copy all files, except for .dockerignore entries
COPY json /opt/ori/json
COPY bin /opt/ori/bin
COPY manage.py /opt/ori/manage.py
COPY ocd_backend /opt/ori/ocd_backend
COPY version.py /opt/ori/ocd_backend/version.py

RUN chown -R 1000:1000 /opt/ori /var/run/celery

# Specify the volume last
# https://docs.docker.com/engine/reference/builder/#notes-about-specifying-volumes
VOLUME /opt/ori/data

WORKDIR /opt/ori
USER celery
CMD celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1
