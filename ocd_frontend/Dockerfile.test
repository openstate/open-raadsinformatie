FROM openstatefoundation/open-raadsinformatie-frontend
MAINTAINER Jurrian Tromp <jurrian@argu.co>

# Change to root for installing
USER root

RUN apk --update add nano

# Install backend testing dependencies
RUN pip install pylint==1.8.4 mock==1.0.1 nose==1.3.4 coverage==4.5.1 Flask-Testing==0.4.2

# Copy frontend testing files
COPY .pylintrc /opt/ori/.pylintrc
COPY tests/__init__.py  /opt/ori/tests/__init__.py
COPY tests/ocd_frontend /opt/ori/tests/ocd_frontend

RUN chown -R 1000:1000 tests .pylintrc

# Switching back to gunicorn user
USER gunicorn
