#!/bin/bash
set -e 

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
iterations=1
ami="ami-a8221fb5"
security_group="sg-9c3281f5"
region="eu-central-1"
ssh_key="rkourtz-nuo"

while [ $iterations -gt 0 ];
do
	for storagebackend in gp2 standard;
	do
	  userdata=`cat $DIR/cloudinit.sh | sed "s/UNKNOWN/${storagebackend}/"`
	  blockdevicemapping="[{\"DeviceName\": \"/dev/xvdb\",  \"Ebs\": {\"VolumeSize\": 50, \"DeleteOnTermination\": true, \"VolumeType\": \"${storagebackend}\", \"Encrypted\": false}}]"
		
	  for type in t2.micro t2.small t2.medium t2.large m3.large m4.large;
		do
		  echo "Launching $type:$storagebackend"
		  aws ec2 run-instances --region $region --image-id $ami --key-name $ssh_key --security-group-ids ${security_group} --user-data "$userdata" --instance-type $type  --associate-public-ip-address --instance-initiated-shutdown-behavior terminate --block-device-mappings "${blockdevicemapping}"
		done
		
  for type in m4.xlarge m3.xlarge c4.large c4.xlarge;
	  do
	    echo "Launching $type:$storagebackend"
	    aws ec2 run-instances --region $region --image-id $ami --key-name $ssh_key --security-group-ids ${security_group} --user-data "$userdata" --instance-type $type  --associate-public-ip-address --instance-initiated-shutdown-behavior terminate --block-device-mappings "${blockdevicemapping}" --ebs-optimized
	  done
	done
	iterations=$((iterations-1))
done
