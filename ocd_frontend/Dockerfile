FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

COPY ocd_frontend/requirements.txt /opt/ori/ocd_frontend/requirements.txt

# Install build base for alpine including gcc for Pillow
RUN apk add --update build-base python-dev py-pip jpeg-dev zlib-dev \
  && pip install --upgrade pip \
  && pip install --no-cache-dir -r /opt/ori/ocd_frontend/requirements.txt \
  && apk del build-base python-dev py-pip

# Create static data folder shared with the backend
RUN mkdir -p /opt/ori/data/static \
  && adduser -D -H gunicorn

# Copy all files, except for .dockerignore entries
COPY ocd_frontend /opt/ori/ocd_frontend
COPY version.py /opt/ori/ocd_frontend/version.py

RUN chown -R 1000:1000 /opt/ori

# Specify the volume last
# https://docs.docker.com/engine/reference/builder/#notes-about-specifying-volumes
VOLUME /opt/ori/data

# For production run the gunicorn wsgi server
USER gunicorn
WORKDIR /opt/ori
CMD gunicorn -w 2 -b 0.0.0.0:5000 ocd_frontend.wsgi
