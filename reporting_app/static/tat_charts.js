
var colour_palette = Highcharts.getOptions().colors;

function format_boxplot_tat(series_name, x, options, time_period, prefix, suffix, nb_decimal) {
    return series_name +
           " -- " +
           format_time_period(time_period, x) +
           ": <br> " +
           format_y_boxplot(options, prefix, suffix, nb_decimal);
}

function draw_highcharts_tat_graphs(data, field_name, time_period){

    aggregated_data = aggregate(
        data,
        field_name,
        ['tat', 'tat', 'tat'],
        [average, boxplot_values_outliers, count],
        ['tat', 'tat_box', 'count'],
        [0, [0], 0]
    );
    function compare_aggregate(a, b){
        return parseInt(a[field_name]) - parseInt(b[field_name]);
    }
    aggregated_data = aggregated_data.sort(compare_aggregate);
    series1 = {
        name: 'Number of sample',
        data: aggregated_data.map(function(d){return [parseInt(d[field_name]), d['count']]}),
        yAxis: 1,
        type: 'column',
        pointPadding: 0.2,
        color: '#CACDD1',
        tooltip: {
            pointFormatter: function(){return format_point_tooltip("", this.x, this.y, time_period, '', 'samples', 0);}
        }
    }
    series2 = {
        name: 'Turn around time',
        data: aggregated_data.map(function(d){return [parseInt(d[field_name])].concat(d.tat_box.values) }),
        yAxis: 0,
        type: 'boxplot',
        color: '#FF4D4D',

        tooltip: {
            pointFormatter: function(){return format_boxplot_tooltip("TAT", this.x, this.options, time_period, '', 'weeks', 1);}
        }
    }
    outliers = aggregated_data.map(function(d){return d.tat_box.outliers.map(function(o){return [parseInt(d[field_name]), o]}); });
    outliers = [].concat.apply([], outliers);
    series3 = {
        name: 'Turn around time',
        data: outliers,
        yAxis: 0,
        type: 'scatter',
        linkedTo: ':previous',
        color: '#FF4D4D',
        marker: {
            enabled: true,
            radius: 2,
            lineWidth: 1
        },
        tooltip: {
            pointFormatter: function(){return format_point_tooltip("TAT", this.x, this.y, time_period, '', 'weeks', 1);}
        }
    }
    series4 = {
        name: 'Avg Turn around time',
        data: aggregated_data.map(function(d){return [parseInt(d[field_name]), d['tat']]}),
        yAxis: 0,
        type: 'line',
        color: '#FF4D4D',
        marker: {
            enable: true,
            symbol: 'square',
            fillColor: '#FF4D4D'
        },
        tooltip: {
            pointFormatter: function(){return format_point_tooltip("avg TAT", this.x, this.y, time_period, '', 'weeks', 1);}
        }
    }
    series = [series1, series2, series3, series4];

    return Highcharts.chart('highchart_cont', {
        chart: {
            zoomType: 'x'
        },
        title: {
            text: 'Turnaround time per ' + time_period,
        },
        xAxis: {
            type: 'datetime',
            title: {
                text: 'Date'
            }
        },
        yAxis: [
            {
                title: {
                    text: 'Turnaround time (weeks)'
                }
            },
            { // Secondary yAxis
                title: {
                    text: 'Number of sample',
                },
                 opposite: true
            }
        ],
        series: series,
        plotOptions: { series: { softThreshold: true }  },
        credits: false
    });
}


// Return the id of the checked radio button base on the button name
function get_radio_value(radio_name){
    var options = document.getElementsByName(radio_name);
    for (var i = 0; i < options.length; i++) {
        if (options[i].checked) {
            return options[i].id;
        }
    }
}


function check_state_and_draw(filtered_data){
    var field_name = get_radio_value("radio_button2") + get_radio_value("radio_button1");
    draw_highcharts_tat_graphs(filtered_data, field_name, get_radio_value("radio_button1") );
}

function all_tat_charts(json){
    // Prepare the data for display
    var finished_data = json.data.filter(function (d){
            return d.current_status === 'finished';
        }).map(function (d) {
        st_date = moment(d['started_date']);
        fi_date = moment(d['finished_date']);
        d['tat'] = moment.duration(fi_date.diff(st_date)).asWeeks();
        ['week', 'month', 'quarter'].forEach(function(time_period) {
            d['st'+time_period] = moment(d['started_date']).startOf(time_period).valueOf();
            d['en'+time_period] = moment(d['finished_date']).startOf(time_period).valueOf();

        });
        return d;
    });


    check_state_and_draw(finished_data);
    ['week', 'month', 'quarter', 'st', 'en', 'mean', 'boxplot'].forEach(function(button_id) {
        $(document).on('change', 'input:radio[id="' + button_id + '"]', function (event) {
            check_state_and_draw(finished_data);
        });
    });
}



// Load the ajax call and call the call back method
function load_ajax_call(url, token, callback){
    $.ajax({
        url: url,
        dataType: "json",
        async: true,
        headers: {'Authorization': token},
        success: function(json) {
            if (callback !== undefined){
                callback(json);
            }
        }
    });
}

// Load the ajax call and call the call back method then show a div and hide the loading message
function load_graph(url, token, callback){
    $('#loadingmessage').show();
    load_ajax_call(url, function(json){
        if (callback !== undefined){
            callback(json);
        }
        $('#loadingmessage').hide();
        $('#plots_div').show();
    })
}
