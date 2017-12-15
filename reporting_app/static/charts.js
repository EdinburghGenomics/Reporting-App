
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

