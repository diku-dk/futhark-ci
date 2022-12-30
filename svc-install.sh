#!/bin/sh

TEMP=$(./svc.sh install)
SVC_NAME=$(echo $TEMP | grep -Po 'actions.runner.*.service')
echo $TEMP
if [ -z $SVC_NAME ]
then
    echo "Could not find name of service."
else
    mkdir "/etc/systemd/system/${SVC_NAME}.d"
    printf "[Service]\nEnvironment=CPATH=/opt/rocm/opencl/include:/usr/local/cuda/include:$CPATH\nEnvironment=LIBRARY_PATH=/opt/rocm/opencl/lib:/usr/local/cuda/lib64:$LIBRARY_PATH\nEnvironment=LD_LIBRARY_PATH=/opt/rocm/opencl/lib:/usr/local/cuda/lib64:$LD_LIBRARY_PATH\n" > "/etc/systemd/system/${SVC_NAME}.d/override.conf"
fi