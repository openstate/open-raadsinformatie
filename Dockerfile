FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

WORKDIR /opt/ori/

COPY ocd_backend/requirements.txt /opt/ori

RUN apk add --update build-base git libxml2-dev libxslt-dev ffmpeg-dev jpeg-dev zlib-dev \
    && pip install --no-cache-dir -r /opt/ori/requirements.txt \
    && apk del build-base git

CMD celery --app=ocd_backend:celery_app worker --loglevel=info --concurrency=1
