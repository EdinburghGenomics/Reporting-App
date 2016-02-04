#!/usr/bin/env bash

scriptpath=$(dirname $(readlink -f $0))
source $scriptpath/init_functions.sh


case $1 in
    start)
        start_flask_app "reporting_app"
        ;;
    stop)
        stop_process "reporting_app"
        ;;
    kill)
        stop_process "reporting_app" kill
        ;;
    restart)
        stop_process "reporting_app"
        start_flask_app "reporting_app"
        ;;
    *)
        echo "usage: $0 (start|stop|kill|restart|log)"
        ;;
esac
echo ""
