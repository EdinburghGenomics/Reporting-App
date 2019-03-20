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
                ret[toGroup]= key;
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
var sum = function (objects, key) { return _.reduce(objects, function (sum, n) { return sum + n[key] }, 0) }
var average = function (objects, key) {return sum(objects, key) / objects.length }
var count = function (objects, key) {return objects.length }
var extract = function (objects, key) { return objects.map( function(d){ return d[key];  }); }
var quantile_box_plot = function (objects, key) {
    return math.quantileSeq(objects.map(function(d){return d[key]}), [0.05, .25, .5, .75, 0.95]);
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
    if (time_period=='week'){return 'Week ' + moment(x).format("w YYYY");}
    if (time_period=='month'){return moment(x).format("MMM YYYY");}
    if (time_period=='quarter'){return 'Q' + moment(x).format("Q YYYY");}
    return ""
}

function format_y_suffix(y, suffix){return y.toFixed(0) + ' ' + suffix}
function format_y_boxplot(options, suffix){
    res = [
       'low:' + options.low.toFixed(0) + ' ' + suffix,
       '25pc:' + options.q1.toFixed(0) + ' ' + suffix,
       'Median:' + options.median.toFixed(0) + ' ' + suffix,
       '75pc:' + options.q3.toFixed(0) + ' ' + suffix,
       'high:' + options.high.toFixed(0) + ' ' + suffix
    ]
    return res.join('<br>');
}
function format_text_tat(x, y, time_period, suffix){
    return format_time_period(time_period, x) + ": " + format_y_suffix(y, suffix);
}

function format_boxplot_tat( x, options, time_period, suffix) {
    return "<b>" + format_time_period(time_period, x) + "<\b>" + ": <br>" + format_y_boxplot(options, suffix);
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
            pointFormatter: function(){return format_text_tat(this.x, this.y, time_period, 'samples');}
        }
    }

    series2 = {
        name: 'Turn around time',
        data: aggregated_data.map(function(d){return [parseInt(d[field_name])].concat(d.tat_box.values) }),
        yAxis: 0,
        type: 'boxplot',
        color: '#FF4D4D',

        tooltip: {
            pointFormatter: function(){return format_boxplot_tat(this.x, this.options, time_period, 'weeks');}
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
            pointFormatter: function(){return format_text_tat(this.x, this.y, time_period, 'weeks');}
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
            pointFormatter: function(){return format_text_tat(this.x, this.y, time_period, 'weeks');}
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


function draw_highcharts_plate_view(title){
Highcharts.chart('container', {

    chart: {
        type: 'heatmap',
        marginTop: 40,
        marginBottom: 80,
        plotBorderWidth: 1
    },
    title: { text: title},
    xAxis: { categories: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] },
    yAxis: { categories: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], title: null},
    colorAxis: {
        min: 0,
        minColor: '#FFFFFF',
        maxColor: Highcharts.getOptions().colors[0]
    },

    legend: {
        align: 'right',
        layout: 'vertical',
        margin: 0,
        verticalAlign: 'top',
        y: 25,
        symbolHeight: 280
    },

    tooltip: {
        formatter: function () {
            return '<b>' + this.series.xAxis.categories[this.point.x] + '</b> sold <br><b>' +
                this.point.value + '</b> items on <br><b>' + this.series.yAxis.categories[this.point.y] + '</b>';
        }
    },

    series: [{
        name: 'Sales per employee',
        borderWidth: 1,
        data: [[0, 0, 10], [0, 1, 19], [0, 2, 8]],
        dataLabels: {
            enabled: true,
            color: '#000000'
        }
    }]

});

}


function draw_plotly_tat_graphs(data, field_name, time_period){

    function compare_aggregate(a, b){
        return parseInt(a[field_name]) - parseInt(b[field_name]);
    }

    aggregated_data = aggregate(data, field_name, 'tat', average);
    aggregated_data = aggregated_data.sort(compare_aggregate);
    var trace1 = {
        x: aggregated_data.map(function(d){return parseInt(d[field_name])}),
        y: aggregated_data.map(function(d){return d['tat']}),
        text: aggregated_data.map(function(d){return format_text_tat(parseInt(d[field_name]), d['tat'], time_period, 'weeks')}),
        type: 'line',
        marker: {color: '#FF4D4D'},
        name: 'Avg Turn around time',
        hoverinfo: 'text'
    };

    sorted_data = data.sort(compare_aggregate);
    var trace2 = {
        x: sorted_data.map(function(d){return parseInt(d[field_name])}),
        y: sorted_data.map(function(d){return d['tat']}),
        y0: 0,
        //text: aggregated_data.map(function(d){return tootltips_format(parseInt(d[field_name]), d['tat'], 'weeks')}),
        type: 'box',
        marker: {
            size: 4,
            color: '#FF4136'
        },
        name: 'Turn around time',
        hoverinfo: 'all'
    };

    aggregated_data = aggregate(data, field_name, 'count', count);
    aggregated_data = aggregated_data.sort(compare_aggregate);
    var trace3 = {
        x: aggregated_data.map(function(d){return parseInt(d[field_name])}),
        y: aggregated_data.map(function(d){return d['count']}),
        text: aggregated_data.map(function(d){return format_text_tat(parseInt(d[field_name]), d['count'], time_period, 'samples')}),
        type: 'bar',
        marker: {color: '#CACDD1'},
        name: 'Number of sample',
        hoverinfo: 'text',
        yaxis: 'y2'
    };

    var data = [ trace1, trace2, trace3 ];

    var selectorOptions = {
        buttons: [{
            step: 'month',
            stepmode: 'backward',
            count: 1,
            label: '1m'
        }, {
            step: 'month',
            stepmode: 'backward',
            count: 6,
            label: '6m'
        }, {
            step: 'year',
            stepmode: 'todate',
            count: 1,
            label: 'YTD'
        }, {
            step: 'year',
            stepmode: 'backward',
            count: 1,
            label: '1y'
        }, {
            step: 'all',
        }],
    };

    var layout = {
        xaxis: {
            type: 'date',
            title: 'Date',
            rangeselector: selectorOptions,
            rangeslider: {visible: false}
        },
        yaxis: {
            title: 'Turnaround time (weeks)',
            overlaying: 'y2',
            fixedrange: true,
        },
        yaxis2: {
            title: 'Number of sample',
            side: 'right',
            fixedrange: true
        },
        title:'Turnaround time per ' + time_period,

    };

    Plotly.purge('plotly_cont');
    return Plotly.plot('plotly_cont', data, layout);
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
    draw_plotly_tat_graphs(filtered_data, field_name, get_radio_value("radio_button1"));
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
    var unfinished_data = data.filter(function (d){
        return d.current_status != 'finished' && d.current_status != 'removed';
    }).map(function (d) {
        st_date = moment(d['started_date']);
        d['tat'] = moment.duration(moment().diff(st_date)).asWeeks();
        ['week', 'month', 'quarter'].forEach(function(time_period) {
            d['st'+time_period] = moment(d['started_date']).startOf(time_period).valueOf();
            d['en'+time_period] = moment().startOf(time_period).valueOf();

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

function aggregate_on_date(run_elements, time_period, fields) {
    var aggregate = {};
    // make dict to aggregate data provided by month and by week
    // for each date that exists in the data provided, set the value as the associated data for that date
    // if data already exists for date corresponding to that key, add the current associated data to the existing values
    var i;
    var data_len = run_elements.length;  // cache the data length to avoid looking it up 30,000 times
    var j;
    var fields_len = fields.length;
    for (i=0; i<data_len; i++) {
        var e = run_elements[i];
        // startOf and endOf have side-effects, so these need to be done on new moment() objects
        var st = moment(e['date']).startOf(time_period);
        var en = moment(e['date']).endOf(time_period);
        var middle_of_time_period = st.add(en.diff(st) / 2);

        if (aggregate[middle_of_time_period] == undefined) {
            aggregate[middle_of_time_period] = {};
            for (j=0; j<fields_len; j++) {
                aggregate[middle_of_time_period][fields[j]] = e[fields[j]];
            }
        } else {
            for (j=0; j<fields_len; j++) {
                aggregate[middle_of_time_period][fields[j]] += e[fields[j]];
            }
        }
    }
    return aggregate
}

function unwind_samples_sequenced(run_elements) {
    var all_sample_data = [];
    var seen_sample_ids = {};

    var i;
    var len = run_elements.length;
    for (i=0; i<len; i++) {
        var e = run_elements[i];
        var sample_id = e['sample_id'];
        var run_id = e['run_id'];
        if (seen_sample_ids[sample_id] == undefined) {
            seen_sample_ids[sample_id] = [run_id];
        } else {
            seen_sample_ids[sample_id].push(run_id);
        }
    }

    var sample;
    var run;
    for (sample in seen_sample_ids) {
        var runs = seen_sample_ids[sample];
        var uniq_runs = _.uniq(runs);
        uniq_runs.sort();
        var repeat_uniq_runs = uniq_runs.slice(1);

        if (uniq_runs.length > 0) {
            all_sample_data.push(
                {
                    'date': moment(uniq_runs[0].split('_')[0], 'YYMMDD').toDate(),
                    'total': 1,
                    'first': 1,
                    'repeat': 0
                }
            );
            for (run in repeat_uniq_runs) {
                all_sample_data.push(
                    {
                        'date': moment(repeat_uniq_runs[run].split('_')[0], 'YYMMDD').toDate(),
                        'total': 1,
                        'first': 0,
                        'repeat': 1
                    }
                );
            }
        }
    }
    return all_sample_data
}

function sortDictByDate(dict){
    var sorted_dict = {};
    var sort = Object.keys(dict).sort(function(a, b) {
        return new Date(a) - new Date(b);
    });
    var sort_aggregate_weeks = sort.map(function(t) {
        sorted_dict[t] = dict[t];
    });
    return sorted_dict
}

function add_cumulative(dict, fields){
    var prev = {};

    var k;
    var i;
    var len = fields.length;
    for (k in dict) {
        for (i=0; i<len; i++) {
            var f = fields[i];
            dict[k]['cumm_' + f] = (prev[f] || 0) + dict[k][f];
            prev[f] = dict[k]['cumm_' + f];
        }
    }
}

// This function will generate a config for a google charts datatable from a dict of values where the key is the
// X axis and the value a dict containing the fields to display.
// Formatting for the X value is given in format_func and fields is a list describing the fields needed
function datatable_config(dict, format_func, fields) {
    var rows = [];
    var cols = [
        {'id': 'Date', 'label': 'Date', 'type': 'date'}
    ];

    var i;
    var len = fields.length;
    for (i=0; i<len; i++) {
        cols.push(
            {
                'id': fields[i]['name'],
                'label': fields[i]['title'] || field['name'],
                'type': fields[i]['type'] || 'number'
            }
        );
    }

    var k;
    var i;
    for (k in dict) {
        var cells = [format_func(k)];
        for (i=0; i<len; i++) {
            cells.push({'v': dict[k][fields[i]['name']]});
        }
        rows.push({'c': cells});
    }
    return {'cols': cols, 'rows': rows}
}

// Format a date as a week
function format_week(dateformat) {
    var d = new Date(dateformat);
    return {
        'v': d,
        'f': 'week ' + moment(d).format('w YYYY') + ' (' + moment(d).startOf('week').format('DD/MM') + ' -  ' + moment(d).endOf('week').format('DD/MM') + ')'
    };
}

// Format a date as a month
function format_month(dateformat) {
    var d = new Date(dateformat);
    return {'v': d, 'f': moment(d).format('MMM YYYY')};
}

// Add a percentage in a list of dict with the provided name
function add_percentage(dict, numerator, denominator, name){
    var k;
    for (k in dict) {
        dict[k][name] = dict[k][numerator]/dict[k][denominator];
    }
}


function merge_dict_of_objects(obj1, obj2){
    var obj3 = {};

    var k;
    var attrname;
    for (k in obj1) {
        obj3[k] = {};
        for (attrname in obj1[k]) { obj3[k][attrname] = obj1[k][attrname]; }
        for (attrname in obj2[k]) { obj3[k][attrname] = obj2[k][attrname]; }
    }
    return obj3;
}

function plotCharts(run_elements) {
    // This function adds a date object in a dict
    run_elements.map(function(element) {
        element['date'] = moment(element['run_id'].split('_')[0], 'YYMMDD');
    });
    // Add filtered data
    run_elements.map(function(element) {
        if (element['useable'] == 'yes') {
            element['useable_yield_in_gb'] = element['yield_in_gb'];
        } else {
            element['useable_yield_in_gb'] = 0;
        }
    });

    var field_names = ['yield_in_gb', 'yield_q30_in_gb', 'useable_yield_in_gb'];

    // Aggregate per month and weeks
    var aggregate_months = sortDictByDate(aggregate_on_date(run_elements, 'month', field_names));
    var aggregate_weeks = sortDictByDate(aggregate_on_date(run_elements, 'week', field_names));
    add_percentage(aggregate_weeks, 'yield_q30_in_gb', 'yield_in_gb', 'ratio_Q30');
    add_percentage(aggregate_months, 'yield_q30_in_gb', 'yield_in_gb', 'ratio_Q30');
    add_percentage(aggregate_weeks, 'useable_yield_in_gb', 'yield_in_gb', 'ratio_useable');
    add_percentage(aggregate_months, 'useable_yield_in_gb', 'yield_in_gb', 'ratio_useable');

    add_cumulative(aggregate_weeks, field_names);
    add_cumulative(aggregate_months, field_names);

    var unwound_samples = unwind_samples_sequenced(run_elements);

    var fields_sample = ['first', 'repeat', 'total'];
    var aggregate_weeks = sortDictByDate(
        merge_dict_of_objects(
            aggregate_weeks,
            aggregate_on_date(unwound_samples, 'week', fields_sample)
        )
    );
    var aggregate_months = sortDictByDate(
        merge_dict_of_objects(
            aggregate_months,
            aggregate_on_date(unwound_samples, 'month', fields_sample)
        )
    );

    var fields = [
        {'name': 'yield_in_gb', 'title': 'Yield'},
        {'name': 'yield_q30_in_gb', 'title': 'Yield Q30'},
        {'name': 'useable_yield_in_gb', 'title': 'Useable yield'},
        {'name': 'ratio_Q30', 'title': '%Q30'},
        {'name': 'ratio_useable', 'title': '% useable'},
        {'name': 'cumm_yield_in_gb', 'title': 'Cumulative Yield'},
        {'name': 'cumm_yield_q30_in_gb', 'title': 'Cumulative Yield Q30'},
        {'name': 'first', 'title': 'First'},
        {'name': 'repeat', 'title': 'Repeat'},
        {'name': 'total', 'title': 'Total'}
    ];

    var run_yield_data_weeks = new google.visualization.DataTable(
        datatable_config(aggregate_weeks, format_week, fields)
    );
    var run_yield_data_months = new google.visualization.DataTable(
        datatable_config(aggregate_months, format_month, fields)
    );

    // draw run charts
    var dashboard = new google.visualization.Dashboard(document.getElementById('dashboard_div'));

    var dateSlider = new google.visualization.ControlWrapper({
        'controlType': 'ChartRangeFilter',
        'containerId': 'control_div',
        'options': {
            'filterColumnIndex': 0,
            'ui': {
                'chartType': 'LineChart',
                'chartOptions': {
                    'height': 50,
                    'chartArea': {'width': '90%'},
                    'hAxis': {'baselineColor': 'none'}
                },
                'chartView': {'columns': [0, 1]}
            }
        },
        'state' : {
            'range': {
                'start': moment().add(-12, 'month').toDate(),
                'end': moment().toDate()
            }
        }
    });
    var yield_chart = new google.visualization.ChartWrapper({
        'chartType': 'ComboChart',
        'containerId': 'run_yield_by_date',
        'view': {'columns': [0, 1, 4, 5]},
        'options': {
            title: 'Run yield',
            series: {
                0: {targetAxisIndex:0, type: 'bars'},
                1: {targetAxisIndex:1, type: 'line', curveType: 'function'},
                2: {targetAxisIndex:1, type: 'line', curveType: 'function'},
            },
            vAxes: {
                0: {title: 'Yield'},
                1: {title: 'Ratio', format: '#%'},
            },
            seriesType: 'bars',
        }
    });
    var samples_sequenced_chart = new google.visualization.ChartWrapper({
        'chartType': 'ColumnChart',
        'containerId': 'samples_sequenced',
        'view': {'columns': [0, 8, 9]},
        'options': {
            title: 'Number of samples sequenced',
            vAxis: {'title': 'Number of Samples'},
            'isStacked' : true
        }
    });
    var yield_cumm_chart = new google.visualization.ChartWrapper({
        'chartType': 'LineChart',
        'containerId': 'cumulative_run_yield_by_date',
        'view': {'columns': [0, 6, 7]},
        'options': {
            title: 'Cumulative run yield ',
            vAxis: {'title': 'Yield'},
            legend:  {'position': 'none'},
        }
    });
    var yield_table = new google.visualization.ChartWrapper({
        'chartType': 'Table',
        'containerId': 'table_run_yield_by_date',
        'options': {
            'sortColumn': 0,
            'sortAscending': false,
            'page': 'enable',
            'pageSize': 20
        }
    });

    dashboard.bind([dateSlider], yield_chart);
    dashboard.bind([dateSlider], samples_sequenced_chart);
    dashboard.bind([dateSlider], yield_cumm_chart);
    dashboard.bind([dateSlider], yield_table);

    dashboard.draw(run_yield_data_weeks);

    $('#ShowRunMonths').click(function() {
        dashboard.draw(run_yield_data_months);
    });
    $('#ShowRunWeeks').click(function() {
        dashboard.draw(run_yield_data_weeks);
    });
}



