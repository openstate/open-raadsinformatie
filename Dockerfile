FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

# Install system requirements
# Second line are used for image creation and uninstalled afterwards
# Third and fourth lines are lib dependencies and fifth line are
# package dependencies
RUN apk add --update \
  build-base git tzdata \
  libxml2-dev libxslt-dev ffmpeg-dev fontconfig-dev jpeg-dev openjpeg-dev \
  zlib-dev openssl-dev libffi-dev poppler-dev \
  inotify-tools libmagic \
  && pip install cython

# Install python requirements
COPY ocd_backend/requirements.txt /opt/ori/requirements.txt
RUN pip install --no-cache-dir -r /opt/ori/requirements.txt

# Cleanup and setting timezone
RUN pip uninstall -y cython \
  && cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

# Setup Celery
RUN adduser -D -H celery \
  && mkdir -p /var/run/celery \
  && chown celery:celery /var/run/celery
USER celery
WORKDIR /opt/ori/
CMD celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1
