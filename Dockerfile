FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

COPY ocd_backend/requirements.txt /opt/ori/requirements.txt

# Install system requirements
# Second line are used for image creation and uninstalled afterwards to reduce
# layer size. Third and fourth lines are lib dependencies and fifth line are
# package dependencies
RUN apk add --update \
  build-base git tzdata \
  libxml2-dev libxslt-dev poppler-dev openssl-dev \
  inotify-tools libmagic \
  && pip install --upgrade pip \
  && pip install cython \
  && pip install --no-cache-dir -r /opt/ori/requirements.txt \
  && pip uninstall -y cython \
  && cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

# Setup Celery
RUN adduser -D -H celery \
  && mkdir -p /var/run/celery \
  && chown celery:celery /var/run/celery

# Copy all files, except for .dockerignore entries
WORKDIR /opt/ori/
COPY . /opt/ori
RUN ln -sf /proc/1/fd/1 /opt/ori/log/backend.err \
  && chown -R celery:celery .
RUN mkdir -p /opt/ori/data/static && chown -R celery:celery /opt/ori/data

USER celery
CMD celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1
