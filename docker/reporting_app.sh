#!/bin/bash
log_file=/opt/reporting_app.log

checkout_param=$1
if [ "$checkout_param" == "-h" ]
then
    echo "Usage: docker run <docker_args> <image_name> <branch_name>" >> $log_file
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
    echo "Found users.sqlite" >> $log_file
    cp -v /opt/etc/users.sqlite /opt/users.sqlite
fi

if [ -d /opt/etc/db ]
then
    echo "Found mongodb database" >> $log_file
    mkdir -p /data
    cp -rv /opt/etc/db /data/
fi

echo "Start mongodb" >> $log_file
/opt/database/mongodb-linux-x86_64-rhel70-3.4.1/bin/mongod > /opt/database/mongod.log &
mongo_pid=$!
echo "Started mongodb in $mongo_pid" >> $log_file
echo "Start reporting app" >> $log_file
REPORTINGCONFIG=/opt/reporting.yaml /opt/python/bin/python bin/run_app.py rest_api &
reporting_pid=$!
echo "Started reporting app in $reporting_pid" >> $log_file

# Load the data to the LIMS if it has been provided
if [ -e /opt/etc/data_for_clarity_lims.yaml ]
then
     echo "Found lims data yaml file" >> $log_file
    REPORTINGCONFIG=/opt/reporting.yaml PYTHONPATH=. /opt/python/bin/python docker/load_data_to_lims_db.py --yaml_file /opt/etc/data_for_clarity_lims.yaml >> $log_file 2>&1
else
    echo "/opt/etc/data_for_clarity_lims.yaml NOT FOUND" >> $log_file
fi

wait $mongo_pid $reporting_pid
