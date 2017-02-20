#!/bin/bash

checkout_param=$1
if [ "$checkout_param" == "-h" ]
then
    echo "Usage: docker run <docker_args> <image_name> <branch_name>"
    exit 0
fi

cd /opt/Reporting-App
git fetch -a
git checkout $checkout_param

/opt/database/mongodb-linux-x86_64-rhel70-3.4.1/bin/mongod > /opt/database/mongod.log &
REPORTINGCONFIG=/opt/reporting.yaml /opt/python/bin/python bin/run_app.py rest_api
