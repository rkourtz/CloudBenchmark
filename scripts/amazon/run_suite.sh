#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

for storagebackend in gp2 standard;
do
  userdata=`cat $DIR/amazon_cloudinit.sh | sed "s/UNKNOWN/${storagebackend}/"`
  blockdevicemapping="[{\"DeviceName\": \"/dev/xvdb\",  \"Ebs\": {\"VolumeSize\": 50, \"DeleteOnTermination\": true, \"VolumeType\": \"${storagebackend}\", \"Encrypted\": false}}]"
	for type in t2.micro t2.small t2.medium t2.large m3.large m4.large;
	do
	  echo "Launching $type:$storagebackend"
	  aws ec2 run-instances --region eu-central-1 --image-id ami-a8221fb5 --key-name rkourtz-nuo --security-group-ids sg-9c3281f5 --user-data "$userdata" --instance-type $type  --associate-public-ip-address --instance-initiated-shutdown-behavior terminate --block-device-mappings "${blockdevicemapping}"
	done
	
	for type in m4.xlarge m3.xlarge c4.large c4.xlarge;
	do
	  echo "Launching $type:$storagebackend"
	  aws ec2 run-instances --region eu-central-1 --image-id ami-a8221fb5 --key-name rkourtz-nuo --security-group-ids sg-9c3281f5 --user-data "$userdata" --instance-type $type  --associate-public-ip-address --instance-initiated-shutdown-behavior terminate --block-device-mappings "${blockdevicemapping}" --ebs-optimized
	done
done
