

function aggregate_on_date(data, time_period, fields){
    var aggregate = {};
    // make dict to aggregate data provided by month and by week
    // for each date that exists in the data provided, set the value as the associated data for that date
    // if data already exists for date corresponding to that key, add the current associated data to the existing values
    for (var e=0; e < data.length; e++) {
        var d = data[e];
        st = moment(d['date']).startOf(time_period);
        en = moment(d['date']).endOf(time_period);
        var middle_of_time_period = st.add(en.diff(st) / 2);
        if(typeof aggregate[middle_of_time_period] == 'undefined'){
            aggregate[middle_of_time_period] = {};
            for (var i = 0; i < fields.length; i++) {
                aggregate[middle_of_time_period][fields[i]['name']] = d[fields[i]['name']];
            }
        } else {
            for (var i = 0; i < fields.length; i++) {
                aggregate[middle_of_time_period][fields[i]['name']] += d[fields[i]['name']];
            }
        }
    }
    return aggregate
}

function unwind_samples_sequenced(sample_data){
    var all_sample_data = [];
    var seen_sample_ids = {};
    for (var e=0; e < sample_data.length; e++) {
        d = sample_data[e];
        sample_id = d['sample_id'];
        run_id = d['run_id']
        if (! (sample_id in seen_sample_ids) ) {
            seen_sample_ids[sample_id] = [run_id]
        } else {
            seen_sample_ids[sample_id].push(run_id)
        }
    }
    for (var key in seen_sample_ids) {
        var runs = seen_sample_ids[key].slice(0);
        var unique_runs = Array.from(new Set(runs));
        unique_runs.sort();
        var repeat_unique_runs = unique_runs.slice(1)

        if (unique_runs.length > 0) {
            all_sample_data.push({'date': moment(unique_runs[0].split("_")[0], "YYMMDD").toDate(),
            'total': 1,
            'first': 1,
            'repeat': 0
            });
            for (run in repeat_unique_runs) {
                all_sample_data.push({
                    'date': moment(repeat_unique_runs[run].split("_")[0], "YYMMDD").toDate(),
                    'total': 1,
                    'first': 0,
                    'repeat': 1
                });
            }
        }
    }
    return all_sample_data
}

function sortDictByDate(dict){
    var sorted_dict = {};
    var sort = (Object.keys(dict)).sort(function(a, b) {
    return new Date(a) - new Date(b);
    });
    var sort_aggregate_weeks = sort.map(function(t){
        sorted_dict[t] = dict[t];
    });
    return sorted_dict
}

function add_cummulative(dict, fields){
    prev = {};
    for (var k1 in dict){
        for (var i = 0; i < fields.length; i++) {
            dict[k1]['cumm_' + fields[i]['name']] = (prev[fields[i]['name']] || 0) + dict[k1][fields[i]['name']];
            prev[fields[i]['name']] = dict[k1]['cumm_' + fields[i]['name']];
        }
    }
}

// This function will generate a google charts datatable from a dict of values where the key will be the
// X axis and the value a dict containing the fields to display.
// The X formating is described in the X format dict and fields is a list discribing the fields that are needed and their format
function datatable_from_dict(dict, X_format, fields){
    var cols = [];
    var rows = [];
    cols.push({
        'id':X_format['name'] || 'Date',
        'label': X_format['name'] || 'Date',
        'type': X_format['type'] || 'date'
    });
    for (var i = 0; i < fields.length; i++) {
        cols.push({
            'id': fields[i]['name'],
            'label': fields[i]['title'] || field['name'],
            'type': fields[i]['type'] || 'number'
        });
    }
    for (var k in dict) {
        var cells = [];
        if (X_format['format'] !== undefined){
            cells.push(X_format['format'](k));
        }else{
            cells.push({'v':new Date(k)});
        }
        for (var i = 0; i < fields.length; i++) {
            if (fields[i]['format'] !== undefined){
                cells.push(
                    field['format'](dict[k][fields[i]['name']])
                );
            }else{
                cells.push({'v': dict[k][fields[i]['name']]});
            }
        }
        rows.push({'c': cells});
    }
    return new google.visualization.DataTable({'cols': cols, 'rows': rows});
}

// Format a date as a week
function format_week(d){
    var m = moment(new Date(d));
    return {
        'v': new Date(d),
        'f': 'week '+ m.format('w YYYY') + ' (' + m.startOf('week').format('DD/MM') + ' -  ' + m.endOf('week').format('DD/MM') + ')'
    } ;
}

// Format a date as a month
function format_month(m){
    return {'v': new Date(m), 'f': moment(new Date(m)).format('MMM YYYY')};
}

// Add a percentage in a list of dict with the provided name
function add_percentage(dict, numerator, denominator, name){
    for (k in dict){
        dict[k][name] = dict[k][numerator]/dict[k][denominator];
    }
}


function merge_dict_of_object(obj1, obj2){
    var obj3 = {};
    for (k in obj1){
        obj3[k]={};
        for (var attrname in obj1[k]) { obj3[k][attrname] = obj1[k][attrname]; }
        for (var attrname in obj2[k]) { obj3[k][attrname] = obj2[k][attrname]; }
    }
    return obj3;
}

function plotCharts(input_data) {
    // This function adds a date object in a dict
    input_data.map(function(element) {
        element['date'] = moment(element['run_id'].split("_")[0], "YYMMDD").toDate();
    });
    // Add filtered data
    input_data.map(function(element) {
        if (element['useable'] == 'yes'){
            element['useable_yield_in_gb'] = element['yield_in_gb'];
        }else{
            element['useable_yield_in_gb'] = 0;
        }
    });

    fields = [
        {'name':'yield_in_gb', 'title': 'Yield'},
        {'name':'yield_q30_in_gb', 'title': 'Yield Q30'},
        {'name': 'useable_yield_in_gb', 'title': 'Useable yield'}
    ];

    // Aggregate per month and weeks
    var aggregate_months = sortDictByDate(aggregate_on_date(input_data, 'month', fields));
    var aggregate_weeks = sortDictByDate(aggregate_on_date(input_data, 'week', fields));
    add_percentage(aggregate_weeks, 'yield_q30_in_gb', 'yield_in_gb', 'ratio_Q30');
    add_percentage(aggregate_months, 'yield_q30_in_gb', 'yield_in_gb', 'ratio_Q30');
    add_percentage(aggregate_weeks, 'useable_yield_in_gb', 'yield_in_gb', 'ratio_useable');
    add_percentage(aggregate_months, 'useable_yield_in_gb', 'yield_in_gb', 'ratio_useable');

    add_cummulative(aggregate_weeks, fields);
    add_cummulative(aggregate_months, fields);

    fields.push({'name':'ratio_Q30', 'title': '%Q30'});
    fields.push({'name':'ratio_useable', 'title': '% useable'});
    fields.push({'name':'cumm_yield_in_gb', 'title': 'Cummulative Yield'});
    fields.push({'name':'cumm_yield_q30_in_gb', 'title': 'Cummulative Yield Q30'});

    fields_sample = [
        {'name':'first', 'title': 'First'},
        {'name':'repeat', 'title': 'Repeat'},
        {'name':'total', 'title': 'Total'}
    ];
    var unwinded_samples = unwind_samples_sequenced(input_data);

    aggregate_weeks = sortDictByDate(
        merge_dict_of_object(
            aggregate_weeks,
            aggregate_on_date(unwinded_samples, 'week', fields_sample)
        )
    );
    aggregate_months = sortDictByDate(
        merge_dict_of_object(
            aggregate_months,
            aggregate_on_date(unwinded_samples, 'month', fields_sample)
        )
    );

    fields.push(...fields_sample);
    var run_yield_data_weeks = datatable_from_dict(aggregate_weeks, {'format': format_week}, fields);
    var run_yield_data_months = datatable_from_dict(aggregate_months, {'format': format_month}, fields);

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
                "end": moment().toDate()
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
                1: {title: 'Ratio', format:"#%"},
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
            vAxis: {title: 'Number of Samples'},
            'isStacked' : true
        }
    });
    var yield_cumm_chart = new google.visualization.ChartWrapper({
        'chartType': 'LineChart',
        'containerId': 'cumulative_run_yield_by_date',
        'view': {'columns': [0, 6, 7]},
        'options': {
            title: 'Cumulative run yield ',
            vAxis: {title: 'Yield'},
            legend:  {'position': 'none'},
        }
    });
    var yield_table = new google.visualization.ChartWrapper({
        'chartType': 'Table',
        'containerId': 'table_run_yield_by_date',
        'options':{
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

    var show_months_cumulative = document.getElementById("ShowRunMonths");
    show_months_cumulative.onclick = function(){dashboard.draw(run_yield_data_months);}
    var show_weeks_cumulative = document.getElementById("ShowRunWeeks");
    show_weeks_cumulative.onclick = function(){dashboard.draw(run_yield_data_weeks);}
}

