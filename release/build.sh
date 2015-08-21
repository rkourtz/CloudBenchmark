#1/bin/bash
[ ! -d /vagrant ] && echo "ERROR: Please run the script ../build_artifact.sh instead of this one" && exit 2

sudo yum -y install git wget libffi libffi-devel openssl-devel gcc make vim git tar zlib-devel bzip2 openssl-devel which nc
cd /tmp
if [ `python --version 2>&1 | grep -c "2.7"` -lt 1 ];
then
  # Install Python 2.7
  [ ! -f Python-2.7.10.tgz ] && wget https://www.python.org/ftp/python/2.7.10/Python-2.7.10.tgz
  tar -xvzf Python-2.7.10.tgz
  cd Python-2.7.10
  sudo ./configure --prefix=/usr --enable-shared --with-system-ffi
#--with-system-expat
  sudo make install
  sudo ln -s /usr/lib/libpython2.7.so.1.0 /lib64/libpython2.7.so.1.0
fi
wget https://bootstrap.pypa.io/ez_setup.py -O - | sudo python
if [ ! -d 'pyinstaller' ];
then
  git clone -b develop https://github.com/pyinstaller/pyinstaller.git
  cd pyinstaller
  sudo python setup.py install
fi
cd /vagrant
sudo python setup.py develop
sudo find /usr/lib -name cacerts.txt -exec chmod 644 {} \;
[ -d /tmp/benchmark ] && rm -rf /tmp/benchmark
mkdir -p /tmp/benchmark
cd /tmp/benchmark
rm -f /vagrant/release/artifacts/benchmark
pyinstaller --distpath=/vagrant/release/artifacts --hidden-import=pkg_resources -F /vagrant/release/benchmark.spec
