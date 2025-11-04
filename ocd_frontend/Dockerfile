# NOTE: Production config (also make any relevant changes to
# Dockerfile-app-dev)


FROM python:3.11-alpine
MAINTAINER Open State Foundation <developers@openstate.eu>

COPY ocd_frontend/requirements.txt /opt/ori/ocd_frontend/requirements.txt

RUN apk add --update \
  build-base git tzdata curl jq \
  libxml2-dev libxslt-dev linux-headers
RUN apk add postgresql-dev gcc python3-dev musl-dev
RUN pip install --upgrade 'pip<24.3.1' \
  && pip install cython==3.0.11 \
  && pip install --no-cache-dir -r /opt/ori/ocd_frontend/requirements.txt \
  && pip uninstall -y cython \
  && cp /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime \
  && echo "Europe/Amsterdam" > /etc/timezone \
  && apk del build-base git tzdata

WORKDIR /opt/ori

ENV FLASK_APP=ocd_frontend/frontend.py
CMD uwsgi --socket 0.0.0.0:5000 --touch-reload=uwsgi-touch-reload --processes 8 -w frontend:app
