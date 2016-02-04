#!/usr/bin/env bash

scriptpath=$(dirname $(readlink -f $0))
source $scriptpath/init_functions.sh

nosql_server=$REPORTINGDBSERVER
nosql_server_config=$REPORTINDBSERVERCONFIG


function start_db_server {
    check_script_exists $nosql_server
    check_running $nosql_server
    echo "Starting nosql server"
    nohup $nosql_server --config $nosql_server_config /dev/null 2>&1 &
    pid=$!
    echo $pid > "$scriptpath/.$(basename $nosql_server).$pid"  # path/to/.thing.5662
    echo "Started nosql server with pid $pid"
}

case $1 in
    start)
        start_db_server
        ;;
    stop)
        stop_process $nosql_server
        ;;
    kill)
        stop_process $nosql_server kill
        ;;
    restart)
        stop_process $nosql_server
        start_db_server
        ;;
    *)
        echo "usage: $0 (start|stop|kill|restart|log)"
        ;;
esac
echo ""
