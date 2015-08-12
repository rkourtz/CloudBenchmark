#!/bin/bash
set -e 

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "TBD"

#nova boot --flavor m1.small --key-name rkourtz-nuo --block-device source=image,id=7686674e-6a84-449c-aac3-a26f1f38e609,dest=volume,size=20,shutdown=remove,bootindex=0 --block-device source=blank,dest=volume,size=50,bootindex=1,shutdown=remove clitest