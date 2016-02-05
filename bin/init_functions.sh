#!/usr/bin/env bash

scriptpath=$(dirname $(readlink -f $0))

pid_file_dir=$REPORTINGPIDS
nosql_server=$REPORTINGDBSERVER
nosql_server_config=$REPORTINDBSERVERCONFIG
python=$REPORTINGPYTHON


function check_script_exists {
    script=$1
    procname=$(basename $script)

    if ! [ -e $script ]
    then
        echo "Could not find script: $script"
        exit 1
    fi
}


function get_pid_file {
    script=$1
    pid_file=$pid_file_dir/.$script.*
    echo $pid_file
}

function get_pid {
    script=$1
    pid_file=$(get_pid_file $script)
    if [ -f $pid_file ]
    then
        echo $pid_file | sed -r 's/.+\.([0-9]+)/\1/'  # path/to/.thing.5662 -> 5662
    fi
}


function check_running {
    script=$1

    pid=$(get_pid $script)
    if [ $pid ]
    then
        echo "$(basename $script) is already running with pid $pid"
        exit 1
    fi
}


function start_db_server {
    check_script_exists $nosql_server
    check_running $nosql_server
    echo "Starting nosql server"
    nohup $nosql_server --config $nosql_server_config /dev/null 2>&1 &
    pid=$!
    echo $pid > "$pid_file_dir/.$(basename $nosql_server).$pid"  # path/to/.thing.5662
    echo "Started nosql server with pid $pid"
}


function start_flask_app {
    app=$1
    runner=$scriptpath/run_app.py

    check_script_exists $runner
    check_running $app
    echo "Starting $app"
    nohup $python $runner $app > /dev/null 2>&1 &
    pid=$!
    echo $pid > $pid_file_dir/.$app.$pid
    echo "Started $app with pid $pid"
}


function stop_process {
    script=$1
    kill=$2
    pid=$(get_pid $script)
    if ! [ $pid ]
    then
        echo "$script is not running"
        exit 0
    fi

    if [ $kill ] && [ $kill == 'kill' ]
    then
        echo "Killing $(basename $script) (pid $pid)"
        k_sig='-9'
    else
        echo "Stopping $(basename $script) (pid $pid)"
        if [ $(echo $script | sed -r 's/.*(\.py).*/\1/') == '.py' ]
        then
            k_sig='-2'
        else
            k_sig=''
        fi
    fi
    kill $k_sig $pid
    rm $(get_pid_file $script)
}
