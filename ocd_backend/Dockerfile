FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

COPY ocd_backend/requirements.txt /opt/ori/ocd_backend/requirements.txt

# Install system requirements
# Second line are used for image creation and uninstalled afterwards to reduce
# layer size. Third and fourth lines are lib dependencies and fifth line are
# package dependencies
RUN apk add --update \
  build-base git tzdata \
  libxml2-dev libxslt-dev poppler-dev \
  inotify-tools libmagic \
  && pip install cython \
  && pip install --no-cache-dir -r /opt/ori/ocd_backend/requirements.txt \
  && pip uninstall -y cython \
  && cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

# Setup Celery
RUN adduser -D -H celery \
  && mkdir -p /var/run/celery \
  && chown celery:celery /var/run/celery

WORKDIR /opt/ori

# Trick to redirect logs to process 1 when running multiple processes
RUN mkdir /opt/ori/log \
  && ln -sf /proc/1/fd/1 /opt/ori/log/stdout

# Create volume for shared static data with the frontend
RUN mkdir -p /opt/ori/data/static

# Legacy support for frontend settings in manage.py
COPY ocd_frontend/rest/settings.py /opt/ori/ocd_frontend/rest/settings.py
RUN touch /opt/ori/ocd_frontend/__init__.py /opt/ori/ocd_frontend/rest/__init__.py

# Copy all files, except for .dockerignore entries
COPY bin /opt/ori/bin
COPY manage.py /opt/ori/manage.py
COPY owltology /opt/ori/owltology
COPY ocd_backend /opt/ori/ocd_backend

# Change permissions before switching to user
RUN chown -R celery:celery /opt/ori
USER celery

# Specify the volume last
# https://docs.docker.com/engine/reference/builder/#notes-about-specifying-volumes
VOLUME /opt/ori/data

CMD celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1
