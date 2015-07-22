#!/bin/bash

for type in t2.micro t2.small t2.medium t2.large m3.large m4.large;
do
  echo "Running $type"
  aws ec2 run-instances --region eu-central-1 --image-id ami-a8221fb5 --key-name rkourtz-nuo --security-group-ids sg-9c3281f5 --user-data "$(cat ~/workspace/CloudBenchmark/scripts/cloudinit.sh)" --instance-type $type  --associate-public-ip-address --instance-initiated-shutdown-behavior terminate
done

for type in m4.xlarge m3.xlarge c4.large c4.xlarge;
do
  echo "Running $type"
  aws ec2 run-instances --region eu-central-1 --image-id ami-a8221fb5 --key-name rkourtz-nuo --security-group-ids sg-9c3281f5 --user-data "$(cat ~/workspace/CloudBenchmark/scripts/cloudinit.sh)" --instance-type $type --ebs-optimized --associate-public-ip-address --instance-initiated-shutdown-behavior terminate
done
