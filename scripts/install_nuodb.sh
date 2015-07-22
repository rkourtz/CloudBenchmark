#!/bin/bash

DOMAIN_PASSWORD="bird"
CFG_DIR="/opt/nuodb/etc"

[ `whoami` != "root" ] && echo "This script muct be run as root" && exit 2

install_bin="XXX"
for tool in yum dpkg;
do
  which $tool &> /dev/null
  [ "$?" -eq "0" ] && install_bin=`which $tool`
done

[ "$install_bin" == "XXX" ] && echo "Could not determine installation command" && exit 2

case `basename ${install_bin}` in
  "dpkg") apt-get -y update; apt-get -y install openjdk-7-jre-headless curl sed;;
  "yum") yum -y install java curl sed;;
esac

version=`curl http://download.nuohub.org/current_version.txt | awk -F "|" '{print $1}' | awk -F "=" '{print $2}' | sed 's/-/./g'`

case `basename ${install_bin}` in
  "dpkg") 
    artifact="http://download.nuohub.org/nuodb_${version}_amd64.deb"; 
    tempfile=/tmp/nuodb.deb;
    install_command="$install_bin -i $tempfile";;
  "yum") 
    artifact="http://download.nuohub.org/nuodb-${version}.x86_64.rpm";
    tempfile=/tmp/nuodb.rpm;
    install_command="$install_bin -y localinstall $tempfile";;
esac

echo "Downloading $artifact"
[ -f $tempfile ] || curl -o $tempfile $artifact
$install_command
sed -ie "s/^[# ]*domainPassword =.*/domainPassword = $DOMAIN_PASSWORD/" ${CFG_DIR}/default.properties
#/etc/init.d/nuoagent start

# Disable THP
for file in /sys/kernel/mm/transparent_hugepage/enabled /sys/kernel/mm/transparent_hugepage/defrag /sys/kernel/mm/redhat_transparent_hugepage/enable /sys/kernel/mm/redhat_transparent_hugepage/defrag;
do
  if [ -f $file ];
  then
    echo never > ${file}
    echo "echo never > ${file}" >> /etc/rc.local
  fi 
done

