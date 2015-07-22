#!/bin/bash

install_bin="XXX"
export NUODB_LIB_DIR=/opt/nuodb/lib64/
export NUODB_INCLUDE_DIR=/opt/nuodb/include/
   
for tool in yum dpkg;
do
  which $tool &> /dev/null
  [ "$?" -eq "0" ] && install_bin=`which $tool`
done

[ "$install_bin" == "XXX" ] && echo "Could not determine installation command" && exit 2

case `basename ${install_bin}` in
  "dpkg") apt-get -y update; apt-get -y install git cmake make gcc g++ psmisc python sysstat;;
  "yum") yum -y groupinstall development; yum -y install git cmake psmisc python;;
esac

cd ~
git clone https://github.com/nuodb/dbt2.git dbt2
cd dbt2
cmake -DDBMS=nuodb
make
make install

mkdir -p /tmp/dbt2/results
/usr/local/bin/dbt2-nuodb-start-db -f
/usr/local/bin/dbt2-nuodb-load-db
#/usr/local/bin/dbt2-run-workload -a nuodb -c 1 -d 10 -w 1 -o /tmp/dbt2/results/$(date +%s)
