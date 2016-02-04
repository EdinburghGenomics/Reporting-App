#!/usr/bin/env bash

scriptpath=$(dirname $(readlink -f $0))
source $scriptpath/init_functions.sh


case $1 in
    start)
        start_flask_app "rest_api"
        ;;
    stop)
        stop_process "rest_api"
        ;;
    kill)
        stop_process "rest_api" kill
        ;;
    restart)
        stop_process "rest_api"
        start_flask_app "rest_api"
        ;;
    *)
        echo "usage: $0 (start|stop|kill|restart|log)"
        ;;
esac
echo ""
