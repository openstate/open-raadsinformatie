FROM python:2.7-alpine
MAINTAINER Jurrian Tromp <jurrian@argu.co>

# Install system requirements
RUN apk add --update build-base git tzdata libxml2-dev libxslt-dev ffmpeg-dev \
  fontconfig-dev jpeg-dev openjpeg-dev zlib-dev openssl-dev libffi-dev inotify-tools libmagic \
  && pip install cython

# Install python requirements
COPY ocd_backend/requirements.txt /opt/ori/requirements.txt
RUN pip install --no-cache-dir -r /opt/ori/requirements.txt

# Install poppler and pdfparser
COPY src/poppler /tmp/poppler
WORKDIR /tmp/poppler/
RUN ./configure --disable-poppler-qt4 --disable-poppler-qt5 --disable-poppler-cpp --disable-gtk-test --disable-splash-output --disable-utils \
  && make \
  && make install

RUN git clone https://github.com/izderadicka/pdfparser.git /tmp/pdfparser
WORKDIR /tmp/pdfparser/
RUN ldconfig /tmp/pdfparser \
  && POPPLER_ROOT=/tmp/poppler python setup.py install

# Cleanup
RUN pip uninstall -y cython \
  && rm -rf /tmp/pdfparser /tmp/poppler \
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
