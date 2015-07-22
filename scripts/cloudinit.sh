#!/bin/bash
set -e
set -x
sed -i '/Defaults\s*requiretty/d' /etc/sudoers
cd /root
wget https://s3.amazonaws.com/nuodb-rackspace/benchmark
chmod +x benchmark
./benchmark
shutdown -h now 