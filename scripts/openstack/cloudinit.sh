#!/bin/bash
# Cloud init script for CentOS 7.
# setup some environment vars for script runtime.
set -e
set -x
WORKING_DIR='/root'
DOWNLOADS=('https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm'  'https://s3.amazonaws.com/nuodb-rackspace/benchmark')
# EPEL repository needs to be installed first. This action adds the repo that
# contains the following two required packages.
PACKAGES=('epel-release-latest-7.noarch.rpm' 'iperf' 'sysbench' 'xfsprogs')
NUODB_BENCHMARK_OPTIONS='-s ceph -n OpenStack'

# Fix sudoers to enable ttys.
/bin/sed -i '/Defaults\s*requiretty/d' /etc/sudoers

# Start in a known location.
cd ${WORKING_DIR}

# Fetch the EPEL rpm to be able to install the required cli tools to support the 
# python based benchmarking suite.
for download in ${DOWNLOADS[@]}
do
    printf "Downloading %s ..." ${download}
    /bin/curl -sO ${download}
    printf "\tDone.\n"
done

# Install packages needed for the benchmarking process.
for package in ${PACKAGES[@]} 
do
    /bin/yum -y install ${package}
done

printf "Configuring secondary storage mount for testing."
if [ -b /dev/vdb ] && grep -q 'vdb' /proc/partitions
then
    mkfs -t xfs /dev/vdb
    mkdir /testvolume
    mount -t xfs /dev/vdb /testvolume
else
    printf "Secondary storage configuration failed ...\tExiting."
    exit 2
fi
# Make sure the hostname is set so the benchmark script does not break
# when looking up the FQDN
internal_ip=$(ip a show eth0|awk '/inet[[:space:]]/ {split($2,ip,"/");printf"%s",ip[1]}')
echo "${internal_ip} $(hostname)" >>/etc/hosts


/bin/chmod +x "${WORKING_DIR}/benchmark"
${WORKING_DIR}/benchmark ${NUODB_BENCHMARK_OPTIONS}

# Clean up after ourselves

/sbin/shutdown -h now 
