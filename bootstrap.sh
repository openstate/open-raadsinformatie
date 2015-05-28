#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

echo "Provisioning"
sudo apt-get update -qq
sudo apt-get install -y -qq python-software-properties
sudo add-apt-repository -y ppa:rwky/redis > /dev/null
sudo apt-get update -qq
sudo apt-get install -y -qq redis-server
sudo apt-get install -y -qq openjdk-7-jre-headless

echo "Installing Elasticsearch"
wget -q https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.4.2.deb
sudo dpkg -i elasticsearch-1.4.2.deb > /dev/null
sudo service elasticsearch start

echo "Installing Elasticsearch head plugin"
sudo /usr/share/elasticsearch/bin/plugin --install mobz/elasticsearch-head

sudo apt-get install -y make libxml2-dev libxslt1-dev libssl-dev libffi-dev libtiff4-dev libjpeg8-dev liblcms2-dev python-dev python-setuptools python-virtualenv git > /dev/null
sudo easy_install -q pip

echo "Installing ffmpeg"
cd /vagrant
sudo ./install_pyav_deps.sh

cd ~
virtualenv -q ocd
chown -R vagrant:vagrant ocd
echo "source /home/vagrant/ocd/bin/activate; cd /vagrant;" >> ~/.bashrc

echo "Installing requirements"
source ocd/bin/activate

cd /vagrant
pip install Cython==0.21.2 && pip install -r requirements.txt

echo "Starting"
./manage.py elasticsearch create_indexes /vagrant/es_mappings/
./manage.py elasticsearch put_template
