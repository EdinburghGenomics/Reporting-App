

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
    return {'v': new Date(d), 'f': 'week '+ moment(new Date(d)).format('w YYYY')};
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
function runCharts(run_data) {

    // This function adds a date object in a dict
    run_data.map(function(element) {
        element['date'] = moment(element['run_id'].split("_")[0], "YYMMDD").toDate();
    });
    fields = [
        {'name':'yield_in_gb', 'title': 'Yield'},
        {'name':'yield_q30_in_gb', 'title': 'Yield Q30'}
    ];

    // Aggregate per month and weeks
    var aggregate_months = sortDictByDate(aggregate_on_date(run_data, 'month', fields));
    var aggregate_weeks = sortDictByDate(aggregate_on_date(run_data, 'week', fields));
    add_percentage(aggregate_weeks, 'yield_q30_in_gb', 'yield_in_gb', 'ratio');
    add_percentage(aggregate_months, 'yield_q30_in_gb', 'yield_in_gb', 'ratio');

    add_cummulative(aggregate_weeks, fields);
    add_cummulative(aggregate_months, fields);

    fields.push({'name':'ratio', 'title': 'Ratio'});
    fields.push({'name':'cumm_yield_in_gb', 'title': 'Cummulative Yield'});
    fields.push({'name':'cumm_yield_q30_in_gb', 'title': 'Cummulative Yield Q30'});

    var run_yield_data_weeks = datatable_from_dict(aggregate_weeks, {'format': format_week}, fields);
    var run_yield_data_months = datatable_from_dict(aggregate_months, {'format': format_month}, fields);

    // google charts options
    var run_yield_options = {
        title: 'Run yield',
        series: {
            0: {targetAxisIndex:0, type: 'bars'},
            1: {targetAxisIndex:0, type: 'bars'},
            2: {targetAxisIndex:1, type: 'line', curveType: 'function'},
        },
        vAxes: {
            0: {title: 'Yield'},
            1: {title: 'Ratio', format:"#%"},
        },
        seriesType: 'bars',
    };

    var cumulative_run_yield_options = {
        title: 'Cumulative run yield ',
        vAxis: {title: 'Yield'},
        legend:  {'position': 'none'},
    };

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
                }
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
        'view': {'columns': [0, 1, 2, 3]},
        'options': run_yield_options
    });
    var yield_cumm_chart = new google.visualization.ChartWrapper({
        'chartType': 'LineChart',
        'containerId': 'cumulative_run_yield_by_date',
        'view': {'columns': [0, 4, 5]},
        'options': cumulative_run_yield_options
    });
    var yield_table = new google.visualization.ChartWrapper({
        'chartType': 'Table',
        'containerId': 'table_run_yield_by_date'
    });


    dashboard.bind([dateSlider], yield_chart);
    dashboard.bind([dateSlider], yield_cumm_chart);
    dashboard.bind([dateSlider], yield_table);

    dashboard.draw(run_yield_data_weeks);

    var show_months_cumulative = document.getElementById("ShowMonths");
    show_months_cumulative.onclick = function(){dashboard.draw(run_yield_data_months);}
    var show_weeks_cumulative = document.getElementById("ShowWeeks");
    show_weeks_cumulative.onclick = function(){dashboard.draw(run_yield_data_weeks);}
}

function unwind_samples_sequenced(sample_data){
    var all_sample_data = [];
    for (var e=0; e < sample_data.length; e++) {
        d = sample_data[e];
        var run_ids = d['all_run_ids'].slice(0);
        var unique_run_ids = Array.from(new Set(run_ids));
        if (unique_run_ids.length > 0){
            unique_run_ids.sort();
            all_sample_data.push({
                'date': moment(unique_run_ids[0].split("_")[0], "YYMMDD").toDate(),
                'total': 1,
                'first': 1,
                'repeat': 0
            });

            for (run in unique_run_ids.slice(1)){
                all_sample_data.push({
                    'date': moment(unique_run_ids[0].split("_")[0], "YYMMDD").toDate(),
                    'total': 1,
                    'first': 0,
                    'repeat': 1
                });
            }
        }
    }
    return all_sample_data
}

function sampleCharts(sample_data) {
    fields = [
        {'name':'first', 'title': 'First'},
        {'name':'repeat', 'title': 'Repeat'},
        {'name':'total', 'title': 'Total'}
    ];
    var unwinded_samples = unwind_samples_sequenced(sample_data);
    var aggregate_weeks = sortDictByDate(aggregate_on_date(unwinded_samples, 'week', fields))
    var aggregate_months = sortDictByDate(aggregate_on_date(unwinded_samples, 'month', fields))

    //construct that datatables
    var sample_data_month = datatable_from_dict(aggregate_months, {'format': format_month}, fields);
    var sample_data_week = datatable_from_dict(aggregate_weeks, {'format': format_week}, fields);

    var samples_sequenced_chart = new google.visualization.LineChart(document.getElementById('samples_sequenced'));
    var samples_sequenced_table = new google.visualization.Table(document.getElementById('table_samples_sequenced'));

    var sample_week_options = {
    title: 'Number of samples sequenced per week',
    hAxis: {title: 'Week Number / Year'},
    vAxis: {title: 'Number of Samples'}};

    var sample_month_options = {
    title: 'Number of samples sequenced per month',
    hAxis: {title: 'Month Number / Year'},
    vAxis: {title: 'Number of Samples'}};

    // draw the chart by month, then have buttons to switch between by-week and by-month view

    samples_sequenced_chart.draw(sample_data_month, sample_month_options);
    samples_sequenced_table.draw(sample_data_month);

    var show_months = document.getElementById("ShowMonths");
    show_months.onclick = function()
    {
        samples_sequenced_chart.draw(sample_data_month, sample_month_options);
        samples_sequenced_table.draw(sample_data_month);
    }
    var show_weeks = document.getElementById("ShowWeeks");
    show_weeks.onclick = function()
    {
        samples_sequenced_chart.draw(sample_data_week, sample_week_options);
        samples_sequenced_table.draw(sample_data_week);
    }
}