#!/bin/bash

# NOTE: this is not used for Dockerization -- please see the Dockerfile

apt-get update
apt-get -y install libfaac-dev libgpac-dev checkinstall libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev librtmp-dev libtheora-dev libvorbis-dev pkg-config yasm zlib1g-dev

cd /tmp

wget http://www.tortall.net/projects/yasm/releases/yasm-1.2.0.tar.gz
tar xvzf yasm-1.2.0.tar.gz
cd yasm-1.2.0
./configure
make
make install

cd ..
git clone --depth 1 git://git.videolan.org/x264
cd x264
./configure --enable-shared
checkinstall --pkgname=x264 --pkgversion="3:$(./version.sh | \
  awk -F'[" ]' '/POINT/{print $4"+git"$5}')" --backup=no --deldoc=yes \
    --fstrans=no --default

cd ..
wget http://downloads.sourceforge.net/opencore-amr/fdk-aac-0.1.0.tar.gz
tar xzvf fdk-aac-0.1.0.tar.gz
cd fdk-aac-0.1.0
./configure --enable-shared
make

checkinstall --pkgname=fdk-aac --pkgversion="0.1.0" --backup=no \
  --deldoc=yes --fstrans=no --default

cd ..
git clone --depth 1 https://chromium.googlesource.com/webm/libvpx
cd libvpx
./configure --enable-shared
make
checkinstall --pkgname=libvpx --pkgversion="1:$(date +%Y%m%d%H%M)-git" --backup=no \
  --deldoc=yes --fstrans=no --default

cd ../x264
make distclean
./configure --enable-static --enable-shared --enable-pic
make
checkinstall --pkgname=x264 --pkgversion="3:$(./version.sh | \
  awk -F'[" ]' '/POINT/{print $4"+git"$5}')" --backup=no --deldoc=yes \
  --fstrans=no --default

cd ..
wget 'http://mirror.ryansanden.com/ffmpeg-d00bc6a8/xvidcore-1.3.2.tar.gz'
tar -xzf xvidcore-1.3.2.tar.gz
cd xvidcore/build/generic
./configure --prefix='/usr/local'
make
make install

cd ..
#git clone --depth 1 git://source.ffmpeg.org/ffmpeg
git clone git://source.ffmpeg.org/ffmpeg.git
cd ffmpeg
git checkout release/2.4

./configure --enable-shared --enable-gpl --enable-libfaac --enable-libmp3lame --enable-libopencore-amrnb \
  --enable-libopencore-amrwb --enable-librtmp --enable-libtheora --enable-libvorbis \
  --enable-libx264 --enable-nonfree --enable-version3  --enable-libxvid
make
make install

ldconfig
