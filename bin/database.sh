#!/usr/bin/env bash

scriptpath=$(dirname $(readlink -f $0))
source $scriptpath/init_functions.sh


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
