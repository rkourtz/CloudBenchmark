#!/bin/bash

[ `whoami` != "root" ] && echo "This script must be run as root" && exit 2

NUODB_DOMAIN_PASSWORD="bird"
NUODB_CFG_DIR="/opt/nuodb/etc"
NUODB_DOWNLOAD_URL="http://download.nuohub.org"
CURRENT_VERSION_URL="${NUODB_DOWNLOAD_URL}/current_version.txt" 
THP_FILES=(/sys/kernel/mm/transparent_hugepage/enabled /sys/kernel/mm/transparent_hugepage/defrag /sys/kernel/mm/redhat_transparent_hugepage/enable /sys/kernel/mm/redhat_transparent_hugepage/defrag)

get_version ()
{
    printf "Getting current NuoDB version "
    version=`curl -s ${CURRENT_VERSION_URL} | awk -F "|" '{sub("-",".",$1); split($1,version,"="); print version[2]}'`
    printf "%s\n" ${version}
}

get_package()
{
    printf "Downloading %s ..." ${1}
    curl -sO ${1}
    printf "\tDone.\n"
}

for tool in yum dpkg
do
  which ${tool} &> /dev/null && install_bin=`which ${tool}`
done

[ ${install_bin:-XXX} == "XXX" ] && echo "Could not determine installation command" && exit 2

case `basename ${install_bin}` in
  "dpkg") apt-get -y update; apt-get -y install openjdk-7-jre-headless curl sed
          get_version
          if [ ${version:-NULL} != "NULL" ] 
          then
              nuodb_package="${NUODB_DOWNLOAD_URL}/nuodb_${version}_amd64.deb" 
              pushd /tmp &> /dev/null
              printf "Installing NuoDB version %s ..." ${version}
              if [ ! -f $(basename ${nuodb_package}) ]
              then
                  get_package ${nuodb_package} && ${install_bin} -i $(basename ${nuodb_package})
              else
                  "${install_bin} -i $(basename ${nuodb_package})"
              fi
              printf "\tDone.\n"
              popd &> /dev/null
          else
              echo "Cannot determine NuoDB version"
              exit 2
          fi
        ;;
  "yum")  ${install_bin} -y install java curl sed
          get_version
          if [ ${version:-NULL} != "NULL" ] 
          then
              nuodb_package="${NUODB_DOWNLOAD_URL}/nuodb-${version}.x86_64.rpm";
              pushd /tmp &>/dev/null
              printf "Installing NuoDB version %s" ${version}
              if [ ! -f $(basename ${nuodb_package}) ]
              then
                  get_package ${nuodb_package} && ${install_bin} -y install $(basename ${nuodb_package})
              else
                 ${install_bin} -y install $(basename ${nuodb_package})
              fi
              printf "\tDone.\n"
              popd &> /dev/null
          else
              echo "Cannot determine NuoDB version"
              exit 2
          fi
        ;;
esac

printf "Setting NuoDB password ... "
sed -ie "s/^[# ]*domainPassword =.*/domainPassword = ${NUODB_DOMAIN_PASSWORD}/" ${NUODB_CFG_DIR}/default.properties
printf "\tDone.\n"

# Disable THP
printf "Disabling Transparent Huge Pages in:"
for file in ${THP_FILES[@]} 
do
  if [ -f ${file} ] 
  then
    printf "\n\t%s " ${file}
    echo never > ${file}
    if ! grep -q "${file}" /etc/rc.local
    then
        printf "and added it to rc.local"
        echo "echo never > ${file}" >> /etc/rc.local
    fi
  fi 
done
