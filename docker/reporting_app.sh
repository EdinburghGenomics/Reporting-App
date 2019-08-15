#!/bin/bash

checkout_param=$1
if [ "$checkout_param" == "-h" ]
then
    echo "Usage: docker run <docker_args> <image_name> <branch_name>"
    exit 0
fi

cd /opt/Reporting-App
git pull
git checkout $checkout_param
/opt/python/bin/pip install -r requirements.txt

mkdir -p /opt/logs/


# Check the etc folder for file that could have been added there.
if [ -e /opt/etc/users.sqlite ]
then
    cp -v /opt/etc/users.sqlite /opt/users.sqlite
fi

if [ -d /opt/etc/db ]
then
    mkdir -p /data
    cp -rv /opt/etc/db /data/
fi


/opt/database/mongodb-linux-x86_64-rhel70-3.4.1/bin/mongod > /opt/database/mongod.log &
REPORTINGCONFIG=/opt/reporting.yaml /opt/python/bin/python bin/run_app.py rest_api

# Load the data to the LIMS if it has been provided
if [ -e /opt/etc/data_for_clarity_lims.yaml ]
then
    REPORTINGCONFIG=/opt/reporting.yaml PYTHONPATH=. /opt/python/bin/python docker/load_data_to_lims_db.py --yaml_file /opt/etc/data_for_clarity_lims.yaml
fi
