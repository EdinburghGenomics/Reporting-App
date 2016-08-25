
function aggregateData(data) {

    // get all dates in input data and add to date_array
    var date_array = []
    var date_map = data.map(function(t){
        var date = moment(new Date(t[0]))
        date_array.push(date)
    });

    // get min and max year, month and week for input data dates
    var min_date = moment.min(date_array)
    var max_date = moment.max(date_array)
    var min_week = min_date.format('W')
    var min_month = min_date.format('M')
    var min_year = min_date.format('Y')
    var number_of_weeks = max_date.diff(min_date, 'weeks') + 1
    var number_of_months = max_date.diff(min_date, 'months') + 1
    var week_range = Array.apply(null, {length: number_of_weeks}).map(Number.call, Number)
    var month_range = Array.apply(null, {length: number_of_months}).map(Number.call, Number)

    var weeks = {}
    var months = {}

    var current_week = min_week
    var current_year = min_year

    // make a blank dict with keys as the week and the year of each week for earliest to latest
    var populate_blank_weeks = week_range.map(function(t){
    if (current_week < 52) {
          weeks[([parseInt(current_week) + '/' + parseInt(current_year)])] = 0
          current_week = parseInt(current_week, 10) + 1

    } else if (current_week == 52) {
          weeks[([parseInt(current_week) + '/' + parseInt(current_year)])] = 0
          current_week = 1
          current_year = parseInt(current_year, 10) + 1
    }
    });

    var current_month = min_month
    var current_year = min_year

    // make a blank dict with keys as the month and the year of each month for earliest to latest
    var populate_blank_months = month_range.map(function(t){
    if (current_month < 12) {
        months[([parseInt(current_month) + '/' + parseInt(current_year)])] = 0
        current_month = parseInt(current_month, 10) + 1
    } else if (current_month == 12) {
        months[([parseInt(current_month) + '/' + parseInt(current_year)])] = 0
        current_month = 1
        current_year = parseInt(current_year, 10) + 1
    }
    });

    var aggregate_weeks = {}
    var aggregate_months = {}

    // make dict to aggregate data provided by month and by week
    // for each date that exists in the data provided, set the value as the associated data for that date
    // if data already exists for date corresponding to that key, add the current associated data to the existing values

    var available_dates = data.map(function(t){
        var week_number = moment(new Date(t[0])).week()
        var month_number = (moment(new Date(t[0])).month()) + 1
        var year_number = moment(new Date(t[0])).year()

        var month_year = ([parseInt(month_number) + '/' + parseInt(year_number)])
        var week_year = (parseInt(week_number) + '/' + parseInt(year_number))
        if(typeof aggregate_weeks[week_year] == 'undefined'){
            aggregate_weeks[week_year] = t[1]
        } else {
            for(var i = 0; i < ((t[1]).length); i++) {
                aggregate_weeks[week_year][i] = aggregate_weeks[week_year][i] + t[1][i]
            }
        }
        if(typeof aggregate_months[month_year] == 'undefined'){
            aggregate_months[month_year] = t[1]
        } else {
            for(var i = 0; i < ((t[1]).length); i++) {
                aggregate_months[month_year][i] = aggregate_months[month_year][i] + t[1][i]
            }
        }
    });

    return [weeks, months, aggregate_weeks, aggregate_months]
}

function runCharts(hist, yield2date) {

    var yield2date_aggregate = aggregateData(yield2date)

    var weeks = yield2date_aggregate[0]
    var months = yield2date_aggregate[1]
    var aggregate_weeks = yield2date_aggregate[2]
    var aggregate_months = yield2date_aggregate[3]

    var by_month_yield_data = []
    var by_week_yield_data = []
    var by_month_yield_data_cumulative = []
    var by_week_yield_data_cumulative = []
    var current_month_cumulative_yield = 0
    var current_week_cumulative_yield = 0

    // for each week/month in time range of input data, check if there is aggregated data available for that month
    // if not, set the value for that week/month as zero
    // keep running total of values to add to cumulative value

    for (var week in weeks) {
        if(week in aggregate_weeks) {
            current_week_cumulative_yield += (parseInt(aggregate_weeks[week]))
            by_week_yield_data.push([week, aggregate_weeks[week][0]])
            by_week_yield_data_cumulative.push([week, current_week_cumulative_yield])
        } else {
            by_week_yield_data.push([week, 0])
            by_week_yield_data_cumulative.push([week, current_week_cumulative_yield])
        }
    }

    for (var month in months) {
        if(month in aggregate_months) {
              current_month_cumulative_yield += parseInt(aggregate_months[month])
              by_month_yield_data.push([month, aggregate_months[month][0]])
              by_month_yield_data_cumulative.push([month, current_month_cumulative_yield])
        } else {
              by_month_yield_data.push([month, 0])
              by_month_yield_data_cumulative.push([month, current_month_cumulative_yield])
        }
    }

    // draw run charts

    var run_yield_data_weeks = new google.visualization.DataTable();
    run_yield_data_weeks.addColumn('string', 'X');
    run_yield_data_weeks.addColumn('number', 'Yield');
    run_yield_data_weeks.addRows(by_week_yield_data);
    var run_yield_options_weeks = {
    title: 'Run yield per week',
    hAxis: {title: 'Week / Year'},
    vAxis: {title: 'Yield'}};

    var run_yield_data_months = new google.visualization.DataTable();
    run_yield_data_months.addColumn('string', 'X');
    run_yield_data_months.addColumn('number', 'Yield');
    run_yield_data_months.addRows(by_month_yield_data);
    var run_yield_options_months = {
    title: 'Run yield per month',
    hAxis: {title: 'Month / Year'},
    vAxis: {title: 'Yield'}};
    var yield_chart = new google.visualization.ColumnChart(document.getElementById('run_yield_by_date'));

    var cumulative_run_yield_data_week = new google.visualization.DataTable();
    cumulative_run_yield_data_week.addColumn('string', 'X');
    cumulative_run_yield_data_week.addColumn('number', 'Yield');
    cumulative_run_yield_data_week.addRows(by_week_yield_data_cumulative);
    var cumulative_run_yield_options_week = {
    title: 'Cumulative run yield per week',
    hAxis: {title: 'Week / Year'},
    vAxis: {title: 'Cumulative Yield'}};

    var cumulative_run_yield_data_month = new google.visualization.DataTable();
    cumulative_run_yield_data_month.addColumn('string', 'X');
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

function sampleCharts(samples_sequenced, hist) {

    var samples_sequenced_aggregate = aggregateData(samples_sequenced)

    var weeks = samples_sequenced_aggregate[0]
    var months = samples_sequenced_aggregate[1]
    var aggregate_weeks = samples_sequenced_aggregate[2]
    var aggregate_months = samples_sequenced_aggregate[3]

    var by_month_samples_data = []
    var by_week_samples_data = []

    // for each date in weeks/months, add to a list the date and each value associated with that date
    // if no data is associated with that date, add to the list the date and zeros instead

    for (var week in weeks) {
        if(week in aggregate_weeks) {
              by_week_samples_data.push([week, aggregate_weeks[week][0], aggregate_weeks[week][1], aggregate_weeks[week][2]])
        } else {
              by_week_samples_data.push([week, 0, 0, 0])
        }
    }

    for (var month in months) {
        if(month in aggregate_months) {
              by_month_samples_data.push([month, aggregate_months[month][0], aggregate_months[month][1], aggregate_months[month][2]])
        } else {
              by_month_samples_data.push([month, 0, 0, 0])
        }
    }

    // draw sample charts

    var sample_data_month = new google.visualization.DataTable();
    sample_data_month.addColumn('string', 'X');
    sample_data_month.addColumn('number', 'First');
    sample_data_month.addColumn('number', 'Repeat');
    sample_data_month.addColumn('number', 'Total');
    sample_data_month.addRows(by_month_samples_data);

    var sample_data_week = new google.visualization.DataTable();
    sample_data_week.addColumn('string', 'X');
    sample_data_week.addColumn('number', 'First');
    sample_data_week.addColumn('number', 'Repeat');
    sample_data_week.addColumn('number', 'Total');
    sample_data_week.addRows(by_week_samples_data);

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