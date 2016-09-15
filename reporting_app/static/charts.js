

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

function cummulative(dict){
    cummul = {};
    prev = {};
    for (var k1 in dict){
        cummul[k1] = {};
        for (var k2 in dict[k1]){
            cummul[k1][k2] = (prev[k2] || 0) + dict[k1][k2];
            prev[k2] = cummul[k1][k2];
        }
    }
    return cummul;
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

// Format a date
function format_week(d){
    return {'v': new Date(d), 'f': 'week '+ moment(new Date(d)).format('w YYYY')};
}

function format_month(m){
    return {'v': new Date(m), 'f': moment(new Date(m)).format('MMM YYYY')};
}

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
    var cum_weeks = cummulative(aggregate_weeks);
    var cum_months = cummulative(aggregate_months);

    add_percentage(aggregate_weeks, 'yield_q30_in_gb', 'yield_in_gb', 'ratio');
    add_percentage(aggregate_months, 'yield_q30_in_gb', 'yield_in_gb', 'ratio');


    //construct that datatables
    var cumulative_run_yield_data_week = datatable_from_dict(cum_weeks, {'format': format_week}, fields);
    var cumulative_run_yield_data_month = datatable_from_dict(cum_months, {'format': format_month}, fields);

    fields.push({'name':'ratio', 'title': 'Ratio'});
    var run_yield_data_weeks = datatable_from_dict(aggregate_weeks, {'format': format_week}, fields);
    var run_yield_data_months = datatable_from_dict(aggregate_months, {'format': format_month}, fields);

    // google charts options
    var run_yield_options_weeks = {
        title: 'Run yield per week',
        hAxis: {title: 'Week / Year'},
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
    var run_yield_options_months = {
        title: 'Run yield per month',
        hAxis: {title: 'Month / Year'},
        series: {
            0: {targetAxisIndex:0, type: 'bars'},
            1: {targetAxisIndex:0, type: 'bars'},
            2: {targetAxisIndex:1, type: 'line', curveType: 'function'},
        },
        vAxes: {
            0: {title: 'Yield'},
            1: {title: 'Ratio', format:"#%"},
        },

    };
    var cumulative_run_yield_options_week = {
        title: 'Cumulative run yield per week',
        hAxis: {title: 'Week / Year'},
        vAxis: {title: 'Cumulative Yield'}
    };
    var cumulative_run_yield_options_month = {
        title: 'Cumulative run yield per month',
        hAxis: {title: 'Month / Year'},
        vAxis: {title: 'Cumulative Yield'}
    };

    // draw run charts
    var yield_chart = new google.visualization.ComboChart(document.getElementById('run_yield_by_date'));
    var cumulative_yield_chart = new google.visualization.LineChart(document.getElementById('cumulative_run_yield_by_date'));
    var yield_table = new google.visualization.Table(document.getElementById('table_run_yield_by_date'));

    yield_chart.draw(run_yield_data_months, run_yield_options_months);
    cumulative_yield_chart.draw(cumulative_run_yield_data_month, cumulative_run_yield_options_month);
    yield_table.draw(run_yield_data_months);

    var show_months_cumulative = document.getElementById("ShowCumulativeRunYieldMonths");
    show_months_cumulative.onclick = function()
    {
        cumulative_yield_chart.draw(cumulative_run_yield_data_month, cumulative_run_yield_options_month);
        yield_chart.draw(run_yield_data_months, run_yield_options_months);
        yield_table.draw(run_yield_data_months);
    }
    var show_weeks_cumulative = document.getElementById("ShowCumulativeRunYieldWeeks");
    show_weeks_cumulative.onclick = function()
    {
        cumulative_yield_chart.draw(cumulative_run_yield_data_week, cumulative_run_yield_options_week);
        yield_chart.draw(run_yield_data_weeks, run_yield_options_weeks);
        yield_table.draw(run_yield_data_weeks);
    }
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