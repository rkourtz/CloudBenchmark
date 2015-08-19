#1/bin/bash
[ ! -d /vagrant ] && echo "ERROR: Please run the script ../build_artifact.sh instead of this one" && exit 2

sudo yum -y install git wget gcc python-devel libffi libffi-devel openssl-devel
cd ~
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
