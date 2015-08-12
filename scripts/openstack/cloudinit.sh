#!/bin/bash


# This script gets run when the instance starts. To run the test suite run "run_suite.sh"

set -e
set -x
sed -i '/Defaults\s*requiretty/d' /etc/sudoers
cd /root
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum -y install xfsprogs wget sysbench
mkfs -t xfs /dev/vdb
mkdir /testvolume
mount -t xfs /dev/vdb /testvolume
wget https://s3.amazonaws.com/nuodb-rackspace/benchmark
chmod +x benchmark
./benchmark -s "UNKNOWN" -n "Openstack"
shutdown -h now 
