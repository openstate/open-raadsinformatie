FROM openstatefoundation/open-raadsinformatie-backend
MAINTAINER Jurrian Tromp <jurrian@argu.co>

# Change to root for installing
USER root

RUN apk --update add nano

# Install backend testing dependencies
RUN pip install --no-warn-conflicts pylint==1.8.4 mock==1.0.1 nose==1.3.4 coverage==4.5.1

# Copy backend testing files
COPY  .pylintrc /opt/ori/.pylintrc
COPY tests/__init__.py  /opt/ori/tests/__init__.py
COPY tests/ocd_backend /opt/ori/tests/ocd_backend

RUN chown -R celery:celery tests

# Switching back to celery user
USER celery
