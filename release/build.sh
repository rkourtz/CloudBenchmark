#1/bin/bash

sudo yum -y install git
cd ~
if [ ! -d 'pyinstaller' ];
then
  git clone -b develop https://github.com/pyinstaller/pyinstaller.git
  cd pyinstaller
  sudo python setup.py install
fi
cd /vagrant
sudo python setup.py develop
sudo chmod 644 /usr/lib/python2.7/site-packages/httplib2-0.9.1-py2.7.egg/httplib2/cacerts.txt
[ -d /tmp/benchmark ] && rm -rf /tmp/benchmark
mkdir -p /tmp/benchmark
cd /tmp/benchmark
rm -rf /vagrant/release/artifacts/*
pyinstaller --distpath=/vagrant/release/artifacts --hidden-import=pkg_resources -F /vagrant/release/benchmark.spec
