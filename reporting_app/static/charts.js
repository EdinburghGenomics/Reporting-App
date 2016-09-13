

function aggregateData(data, time_period) {
    var data = data;
    var time_period = time_period;
    var aggregate = {};
    // make dict to aggregate data provided by month and by week
    // for each date that exists in the data provided, set the value as the associated data for that date
    // if data already exists for date corresponding to that key, add the current associated data to the existing values

    for (var element=0; element < data.length; element++) {
        var d = data[element]


        var start_of_time_period = (moment(new Date(d[0]))).startOf(time_period).add(1, 'days');
        if(typeof aggregate[start_of_time_period] == 'undefined'){
            aggregate[start_of_time_period] = d[1];
        } else {
            for(var i = 0; i < ((d[1]).length); i++) {
                aggregate[start_of_time_period][i] += d[1][i];
            }
        }
    }
    return aggregate
}

function sortDictByDate(dict){
    var sorted_dict = {}
    var sort = (Object.keys(dict)).sort(function(a, b) {
    return new Date(a) - new Date(b);
    });
    var sort_aggregate_weeks = sort.map(function(t){
        sorted_dict[t] = dict[t]
    });
    return sorted_dict
}

function runCharts(yield2date) {
    var yield2date = yield2date
    var date_map = yield2date.map(function(t){
        (t[0]) = (new Date(t[0]))
    });

    var by_month_yield_data = []
    var by_week_yield_data = []
    var by_month_yield_data_cumulative = []
    var by_week_yield_data_cumulative = []
    var current_month_cumulative_yield = 0
    var current_week_cumulative_yield = 0

    // format dates and yield for google charts
    // keep running total of values to add to cumulative value

    var aggregate_months = sortDictByDate(aggregateData(yield2date, 'month'))
    var aggregate_weeks = sortDictByDate(aggregateData(yield2date, 'week'))


    for (var x in aggregate_weeks) {
        by_week_yield_data.push([new Date(x), aggregate_weeks[x][0]])
        current_week_cumulative_yield += (parseInt(aggregate_weeks[x][0]))
        by_week_yield_data_cumulative.push([new Date(x), current_week_cumulative_yield])
    }

    for (var y in aggregate_months) {
        by_month_yield_data.push([new Date(y), aggregate_months[y][0]])
        current_month_cumulative_yield += (parseInt(aggregate_months[y][0]))
        by_month_yield_data_cumulative.push([new Date(y), current_month_cumulative_yield])
    }

    // draw run charts

    var run_yield_data_weeks = new google.visualization.DataTable();
    run_yield_data_weeks.addColumn('date', 'X');
    run_yield_data_weeks.addColumn('number', 'Yield');
    run_yield_data_weeks.addRows(by_week_yield_data);
    var run_yield_options_weeks = {
    title: 'Run yield per week',
    hAxis: {title: 'Week / Year'},
    vAxis: {title: 'Yield'}};

    var run_yield_data_months = new google.visualization.DataTable();
    run_yield_data_months.addColumn('date', 'X');
    run_yield_data_months.addColumn('number', 'Yield');
    run_yield_data_months.addRows(by_month_yield_data);
    var run_yield_options_months = {
    title: 'Run yield per month',
    hAxis: {title: 'Month / Year'},
    vAxis: {title: 'Yield'}};
    var yield_chart = new google.visualization.ColumnChart(document.getElementById('run_yield_by_date'));



    var cumulative_run_yield_data_week = new google.visualization.DataTable();
    cumulative_run_yield_data_week.addColumn('date', 'X');
    cumulative_run_yield_data_week.addColumn('number', 'Yield');
    cumulative_run_yield_data_week.addRows(by_week_yield_data_cumulative);
    var cumulative_run_yield_options_week = {
    title: 'Cumulative run yield per week',
    hAxis: {title: 'Week / Year'},
    vAxis: {title: 'Cumulative Yield'}};

    var cumulative_run_yield_data_month = new google.visualization.DataTable();
    cumulative_run_yield_data_month.addColumn('date', 'X');
    cumulative_run_yield_data_month.addColumn('number', 'Yield');
    cumulative_run_yield_data_month.addRows(by_month_yield_data_cumulative);
    var cumulative_run_yield_options_month = {
    title: 'Cumulative run yield per month',
    hAxis: {title: 'Month / Year'},
    vAxis: {title: 'Cumulative Yield'}};
    var cumulative_yield_chart = new google.visualization.LineChart(document.getElementById('cumulative_run_yield_by_date'));


    yield_chart.draw(run_yield_data_months, run_yield_options_months);
    cumulative_yield_chart.draw(cumulative_run_yield_data_month, cumulative_run_yield_options_month);

    var show_months_cumulative = document.getElementById("ShowCumulativeRunYieldMonths");
    show_months_cumulative.onclick = function()
    {
    cumulative_yield_chart.draw(cumulative_run_yield_data_month, cumulative_run_yield_options_month);
    yield_chart.draw(run_yield_data_months, run_yield_options_months);
    }
    var show_weeks_cumulative = document.getElementById("ShowCumulativeRunYieldWeeks");
    show_weeks_cumulative.onclick = function()
    {
    cumulative_yield_chart.draw(cumulative_run_yield_data_week, cumulative_run_yield_options_week);
    yield_chart.draw(run_yield_data_weeks, run_yield_options_weeks);
    }
}

function sampleCharts(samples_sequenced) {

    var aggregate_weeks = sortDictByDate(aggregateData(samples_sequenced, 'week'))
    var aggregate_months = sortDictByDate(aggregateData(samples_sequenced, 'month'))

    var one = []
    var two = []

    for (var week in aggregate_weeks) {
        one.push([new Date(week), aggregate_weeks[week][0], aggregate_weeks[week][1], aggregate_weeks[week][2]])
    }

    for (var month in aggregate_months) {
        two.push([new Date(month), aggregate_months[month][0], aggregate_months[month][1], aggregate_months[month][2]])
    }


    var sample_data_month = new google.visualization.DataTable();
    sample_data_month.addColumn('date', 'X');
    sample_data_month.addColumn('number', 'First');
    sample_data_month.addColumn('number', 'Repeat');
    sample_data_month.addColumn('number', 'Total');
    sample_data_month.addRows(two);

    var sample_data_week = new google.visualization.DataTable();
    sample_data_week.addColumn('date', 'X');
    sample_data_week.addColumn('number', 'First');
    sample_data_week.addColumn('number', 'Repeat');
    sample_data_week.addColumn('number', 'Total');
    sample_data_week.addRows(one);

    var samples_sequenced_chart = new google.visualization.LineChart(document.getElementById('samples_sequenced'));

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

    var show_months = document.getElementById("ShowMonths");
    show_months.onclick = function()
    {
    view = new google.visualization.DataView(sample_data_month);
    samples_sequenced_chart.draw(sample_data_month, sample_month_options);
    }
    var show_weeks = document.getElementById("ShowWeeks");
    show_weeks.onclick = function()
    {
    view = new google.visualization.DataView(sample_data_week);
    samples_sequenced_chart.draw(sample_data_week, sample_week_options);
    }
}