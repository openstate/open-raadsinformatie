FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

#RUN mkdir -p /opt/ori
COPY . /opt/ori/ocd_frontend
WORKDIR /opt/ori/ocd_frontend

# Install build base for alpine including gcc for Pillow
RUN apk add --update build-base python-dev py-pip jpeg-dev zlib-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del build-base python-dev py-pip

CMD python wsgi.py
