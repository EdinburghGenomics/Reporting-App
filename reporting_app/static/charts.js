
var colour_palette = Highcharts.getOptions().colors;

//get any percentile from an array
function getPercentile(data, percentile) {
    data.sort(numSort);
    var index = (percentile / 100) * data.length;
    var result;
    if (Math.floor(index) == index) {
        result = (data[(index - 1)] + data[index]) / 2;
    } else {
        result = data[Math.floor(index)];
    }
    return result;
}

//because .sort() doesn't sort numbers correctly
function numSort(a, b) {
  return a - b;
}

function aggregate(list_object, toGroup, toAggregate, fn, output_field, val0) {
    /*
    use lodash.js to group, and aggregate the data
    list_object: list of object to aggregate
    toGroup: field used to group the object
    toAggregate: field or list of field to aggregate and report after grouping
    fn: function or list of function to calculate the aggregate
    output_field: field or list of field to name the aggregated fields default to toAggregate
    val0: value of list of value used as default for each field.
    */
    if (output_field === undefined){output_field=toAggregate;}
    return _.chain(list_object)
            .groupBy(toGroup)
            .map(function(g, key) {
                ret = {}
                // Because the key has been used as an object property, it has been cast to a string.
                ret[toGroup] = key;
                if (Array.isArray(toAggregate)){
                    for (var i=0; i < toAggregate.length; i++) {
                        ret[output_field[i]] = fn[i](g, toAggregate[i]) || val0[i] || 0;
                    }
                }else{
                        ret[output_field] = fn(g, toAggregate) || val0 || 0;
                }
                return ret;
            })
            .value();
    }

/*Functions for aggregation in the underscore pipeline*/
var sum = function (objects, key) { return _.reduce(objects, function (sum, n) { return sum + _.get(n, key) }, 0) }
var average = function (objects, key) {return sum(objects, key) / objects.length }
var count = function (objects, key) {return objects.length }
var extract = function (objects, key) { return objects.map( function(d){ return _.get(d, key);  }); }
var quantile_box_plot = function (objects, key) {
    return math.quantileSeq(objects.map(function(d){return _.get(d, key)}), [0.05, .25, .5, .75, 0.95]);
}
var boxplot_values_outliers = function(objects, key) {
    var data = extract(objects, key);
    var boxData = {},
        min = Math.min.apply(Math, data),
        max = Math.max.apply(Math, data),
        q1 = getPercentile(data, 25),
        median = getPercentile(data, 50),
        q3 = getPercentile(data, 75),
        iqr = q3 - q1,
        lowerFence = q1 - (iqr * 1.5),
        upperFence = q3 + (iqr * 1.5),
        outliers = [];
        in_dist_data = [];

    for (var i = 0; i < data.length; i++) {
        if (data[i] < lowerFence || data[i] > upperFence) {
            outliers.push(data[i]);
        }else{
            in_dist_data.push(data[i])
        }
    }
    boxData.values = [Math.min.apply(Math, in_dist_data), q1, median, q3, Math.max.apply(Math, in_dist_data)];
    boxData.outliers = outliers;
    return boxData;
}

/*Functions for formating tooltip text from a data point*/
function format_time_period(time_period, x) {
    if (time_period=='date'){return moment(x).format("DD MMM YYYY");}
    if (time_period=='week'){return 'Week ' + moment(x).format("w YYYY");}
    if (time_period=='month'){return moment(x).format("MMM YYYY");}
    if (time_period=='quarter'){return 'Q' + moment(x).format("Q YYYY");}
    return ""
}

function format_y_suffix(y, prefix, suffix){return prefix + ' ' + y.toFixed(1) + ' ' + suffix}
function format_y_boxplot(options, prefix, suffix){
    res = [
       'low: ' + prefix + ' ' + options.low.toFixed(0) + ' ' + suffix,
       '25pc: ' + prefix + ' '  + options.q1.toFixed(0) + ' ' + suffix,
       'Median: ' + prefix + ' '  + options.median.toFixed(0) + ' ' + suffix,
       '75pc: ' + prefix + ' '  + options.q3.toFixed(0) + ' ' + suffix,
       'high: ' + prefix + ' '  + options.high.toFixed(0) + ' ' + suffix
    ]
    return res.join('<br>');
}
function format_text_tat(series_name, x, y, time_period, prefix,  suffix){
    return  series_name + " --  " + format_time_period(time_period, x) + ": <br> " + format_y_suffix(y, prefix, suffix);
}

function format_boxplot_tat(series_name, x, options, time_period, prefix, suffix) {
    return series_name + " -- " + format_time_period(time_period, x) + ": <br> " + format_y_boxplot(options, prefix, suffix);
}

function draw_highcharts_tat_graphs(data, field_name, time_period){

    aggregated_data = aggregate(
        data,
        field_name,
        ['tat', 'tat', ''],
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
            pointFormatter: function(){return format_text_tat("", this.x, this.y, time_period, '', 'samples');}
        }
    }

    series2 = {
        name: 'Turn around time',
        data: aggregated_data.map(function(d){return [parseInt(d[field_name])].concat(d.tat_box.values) }),
        yAxis: 0,
        type: 'boxplot',
        color: '#FF4D4D',

        tooltip: {
            pointFormatter: function(){return format_boxplot_tat("", this.x, this.options, time_period, '', 'weeks');}
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
            pointFormatter: function(){return format_text_tat("", this.x, this.y, time_period, '', 'weeks');}
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
            pointFormatter: function(){return format_text_tat("", this.x, this.y, time_period, '', 'weeks');}
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

function all_tat_charts(data){
    // Prepare the data for display
    var finished_data = data.filter(function (d){
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

function get_categories(data, key){
    var categories = _.uniq(data.map(function(d) {return _.get(d, key)}))
    categories.sort()
    return categories
}

function box_plot_series(data, color_key, metric_path, metric_name){
    // Generate a box plot with outliers series  based on the provided color key and metric
    var series = []
    var i = 0;

    color_categories = get_categories(data, color_key)

    color_categories.map(function(category){

        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        var aggregated_data = aggregate(filtered_data, 'date', metric_path, boxplot_values_outliers, 'metric_box', [0])
        outliers = aggregated_data.map(function(d){return d.metric_box.outliers.map(function(o){return [parseInt(d['date']), o]}); });
        outliers = [].concat.apply([], outliers);
        values = aggregated_data.map(function(d){return [parseInt(d['date'])].concat(d.metric_box.values)})

        series.push({
            name: category,
            data: aggregated_data.map(function(d){return [parseInt(d['date'])].concat(d.metric_box.values)}),
            yAxis: 0,
            type: 'boxplot',
            tooltip: {
                pointFormatter: function(){return format_boxplot_tat(color_key + " " + category, this.x, this.options, 'date', metric_name, '');}
            },
            color: colour_palette[i],
        })
        series.push({
            name: category,
            data: outliers,
            yAxis: 0,
            type: 'scatter',
            linkedTo: ':previous',
            marker: {
                enabled: true,
                radius: 2,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_text_tat(color_key + " " + category, this.x, this.y, 'date', metric_name, '');}
            },
            color: colour_palette[i],
        })
        i += 1;
    })
    return series
}

function scatter_series(data, color_key, metric_path, metric_name){
    // Generate a plot with scatter series based on the provided color key and metric
    // No aggregation is performed

    color_categories = get_categories(data, color_key)
    return color_categories.map(function(category){
        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        return {
            name: category,
            data: _.map(filtered_data, function(d){return [parseInt(d['date']), _.get(d, metric_path)] }),
            yAxis: 0,
            type: 'scatter',
            marker: {
                enabled: true,
                radius: 5,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_text_tat(color_key + " " + category, this.x, this.y, 'date', metric_name, '');}
            }
        }
    })

}

function average_series(data, color_key, metric_path, metric_name){
    // Generate a plot series showing average of the provided color key and metric
    color_categories = get_categories(data, color_key)

    return color_categories.map(function(category){

        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        var aggregated_data = aggregate(filtered_data, 'date', metric_path, average, 'metric_avg', null)
        return {
            name: category,
            data: aggregated_data.map(function(d){return [parseInt(d['date']), d['metric_avg']]}),
            yAxis: 0,
            type: 'line',
            marker: {
                enabled: true,
                radius: 5,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_text_tat(color_key + " " + category, this.x, this.y, 'date', metric_name, '');}
            }
        }
    })
}


function lane_sequencing_metrics_chart(data){
    // Adds date and sequencer to the data structure by parsing the run name
    data.map(function(element) {
        element['date'] = moment(element['run_id'].split('_')[0], 'YYMMDD').valueOf();
        element['sequencer'] = element['run_id'].split('_')[1];
    });
    metric_path = 'aggregated.pc_duplicate_reads'
    metric_name = '%duplicates'
    color_metric = 'lane_number'

//    var series = box_plot_series(data, color_metric, metric_path, metric_name)
//    var series = scatter_series(data, color_metric, metric_path, metric_name)
    var series = average_series(data, color_metric, metric_path, metric_name)
    return Highcharts.chart('highchart_cont', {
        chart: {
            zoomType: 'x'
        },
        title: {
            text: 'Sequencing metrics: ' + metric_name,
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
                    text: metric_name
                }
            },
        ],
        series: series,
        credits: false
    });

}

// Load the ajax call and call the call back method
function load_graph(url, token, callback){
    $('#loadingmessage').show();
    $.ajax({
        url: url,
        dataType: "json",
        async: true,
        headers: {'Authorization': token},
        success: function(json) {
            $('#loadingmessage').hide();
            callback(json['data']);
            $('#plots_div').show();
        }
    });
}