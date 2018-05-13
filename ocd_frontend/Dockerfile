FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

WORKDIR /opt/ori
COPY ocd_frontend/requirements.txt /opt/ori/ocd_frontend/requirements.txt

# Install build base for alpine including gcc for Pillow
RUN apk add --update build-base python-dev py-pip jpeg-dev zlib-dev \
    && pip install --no-cache-dir -r /opt/ori/ocd_frontend/requirements.txt \
    && apk del build-base python-dev py-pip

# Create volume for shared static data with the backend
VOLUME /opt/ori/data
RUN mkdir -p /opt/ori/data/static

# Copy all files, except for .dockerignore entries
COPY ocd_frontend /opt/ori/ocd_frontend

RUN chown -R nobody:nobody /opt/ori
USER nobody

# For production run the gunicorn wsgi server
CMD gunicorn -w 2 -b 0.0.0.0:5000 ocd_frontend.wsgi
