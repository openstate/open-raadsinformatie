FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

WORKDIR /opt/ori/ocd_frontend
COPY requirements.txt /opt/ori/ocd_frontend/requirements.txt

# Install build base for alpine including gcc for Pillow
RUN apk add --update build-base linux-headers python-dev py-pip jpeg-dev zlib-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del build-base linux-headers python-dev py-pip

COPY . /opt/ori/ocd_frontend

CMD python wsgi.py
