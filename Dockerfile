FROM ubuntu:14.04
MAINTAINER Sicco van Sas <sicco@openstate.eu>

# Use bash as default shell
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Add multiverse to sources
RUN echo 'deb http://archive.ubuntu.com/ubuntu/ precise multiverse' >> etc/apt/sources.list

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

#Set Timezone
RUN echo "Europe/Amsterdam" > /etc/timezone \
    && dpkg-reconfigure -f noninteractive tzdata

RUN apt-get update \
    && apt-get install -y \
        python-dev \
        python-setuptools \
        python-software-properties \
        openjdk-7-jre-headless \
        wget \
        curl \
        poppler-utils \
        software-properties-common \
        gettext \
        git \
        vim

# according to http://www.monblocnotes.com/node/2057
RUN sed -i 's/exit 101/exit 0/' /usr/sbin/policy-rc.d

# according to http://www.monblocnotes.com/node/2057
RUN sed -i 's/exit 101/exit 0/' /usr/sbin/policy-rc.d

RUN apt-get install -y redis-server
RUN service redis-server start

# Install elasticsearch
ENV ES_VERSION 1.4.2
RUN wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-${ES_VERSION}.deb
RUN dpkg -i elasticsearch-${ES_VERSION}.deb > /dev/null
RUN sed -i 's/#discovery.zen.ping.multicast.enabled: false/discovery.zen.ping.multicast.enabled: false/' /etc/elasticsearch/elasticsearch.yml
RUN service elasticsearch start
RUN rm elasticsearch-${ES_VERSION}.deb

# Install elasticsearch head plugin
RUN /usr/share/elasticsearch/bin/plugin --install mobz/elasticsearch-head

RUN apt-get install -y \
        make \
        libxml2-dev \
        libxslt1-dev \
        libssl-dev \
        libffi-dev \
        libtiff4-dev \
        libjpeg8-dev \
        liblcms2-dev \
        python-dev \
        python-setuptools \
        python-virtualenv \
        git \
        supervisor \
        vim

RUN easy_install pip

##### Install dependencies for pyav #####
RUN apt-get install -y \
        libfaac-dev \
        libgpac-dev \
        checkinstall \
        libmp3lame-dev \
        libopencore-amrnb-dev \
        libopencore-amrwb-dev \
        librtmp-dev \
        libtheora-dev \
        libvorbis-dev \
        pkg-config \
        yasm \
        zlib1g-dev

# Temporarily use /tmp as workdir for the pyav dependencies
WORKDIR /tmp

ENV YASM_VERSION 1.2.0
RUN curl -sSL http://www.tortall.net/projects/yasm/releases/yasm-${YASM_VERSION}.tar.gz | \
        tar -xz \
    && cd yasm-${YASM_VERSION} \
    && ./configure \
    && make \
    && make install

#ENV x264_COMMIT 121396c71b4907ca82301d1a529795d98daab5f8
RUN git clone --depth 1 git://git.videolan.org/x264 \
    && cd x264 \
#&& git checkout -q $x264_COMMIT \
    && ./configure --enable-shared \
    && checkinstall \
        --pkgname=x264 \
        --pkgversion="3:$(./version.sh | awk -F'[" ]' '/POINT/{print $4"+git"$5}')" \
        --backup=no \
        --deldoc=yes \
        --fstrans=no \
        --default

ENV FDKAAC_VERSION 0.1.0
RUN curl -sSL http://downloads.sourceforge.net/opencore-amr/fdk-aac-${FDKAAC_VERSION}.tar.gz | \
        tar -xz \
    && cd fdk-aac-${FDKAAC_VERSION} \
    && ./configure --enable-shared \
    && make \
    && checkinstall \
        --pkgname=fdk-aac \
        --pkgversion=${FDKAAC_VERSION} \
        --backup=no \
        --deldoc=yes \
        --fstrans=no \
        --default

#ENV LIBVPX_COMMIT ccc9e1da8d1ef03a471ab227e1049cd55bebd806
RUN git clone --depth 1 https://chromium.googlesource.com/webm/libvpx \
    && cd libvpx \
#&& git checkout -q $LIBVPX_COMMIT \
    && ./configure --enable-shared \
    && make \
    && checkinstall \
        --pkgname=libvpx \
        --pkgversion="1:$(date +%Y%m%d%H%M)-git" \
        --backup=no \
        --deldoc=yes \
        --fstrans=no \
        --default

RUN cd x264 \
    && make distclean \
    && ./configure --enable-static --enable-shared --enable-pic \
    && make \
    && checkinstall \
        --pkgname=x264 \
        --pkgversion="3:$(./version.sh | awk -F'[" ]' '/POINT/{print $4"+git"$5}')" \
        --backup=no \
        --deldoc=yes \
        --fstrans=no \
        --default

ENV XVIDCORE_VERSION 1.3.2
RUN curl -sSL http://mirror.ryansanden.com/ffmpeg-d00bc6a8/xvidcore-${XVIDCORE_VERSION}.tar.gz | \
        tar -xz \
    && cd xvidcore/build/generic \
    && ./configure --prefix='/usr/local' \
    && make \
    && make install

#ENV FFMPEG_COMMIT 580c86925ddf8c85d2e6f57ed55dd75853748b29
RUN git clone git://source.ffmpeg.org/ffmpeg.git \
    && cd ffmpeg \
    && git checkout release/2.4 \
#&& git checkout -q $FFMPEG_COMMIT \
    && ./configure \
        --enable-shared \
        --enable-gpl \
        --enable-libfaac \
        --enable-libmp3lame \
        --enable-libopencore-amrnb \
        --enable-libopencore-amrwb \
        --enable-librtmp \
        --enable-libtheora \
        --enable-libvorbis \
        --enable-libx264 \
        --enable-nonfree \
        --enable-version3 \
        --enable-libxvid \
    && make \
    && make install \
    && ldconfig
##########

WORKDIR /opt/ori
# Create a virtualenv project
RUN echo 'ok'
RUN virtualenv -q /opt
RUN echo "source /opt/bin/activate; cd /opt/ori;" >> ~/.bashrc

# Temporarily add all NPO Backstage files on the host to the container
# as it contains files needed to finish the base installation
ADD . /opt/ori

# Install Python requirements
RUN source ../bin/activate \
    && pip install Cython==0.21.2 \
    && pip install -r requirements.txt

# Start
RUN source ../bin/activate \
    && service elasticsearch restart \
    && sleep 20 \
    && ./manage.py elasticsearch create_indexes es_mappings/ \
    && ./manage.py elasticsearch put_template

RUN apt-get install supervisor

# Delete all NPO Bastage files again
RUN find . -delete

# When the container is created or started run start.sh which starts
# all required services and supervisor which starts celery and celerycam
CMD /opt/ori/start.sh
