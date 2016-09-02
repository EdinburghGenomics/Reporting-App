
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
          weeks[moment().year(current_year).week(current_week).day("Monday")] = 0
          current_week = parseInt(current_week, 10) + 1
    } else if (current_week == 52) {
          weeks[moment().year(current_year).week(current_week).day("Monday")] = 0
          current_week = 1
          current_year = parseInt(current_year, 10) + 1
    }
    });

    var current_month = min_month
    var current_year = min_year

    // make a blank dict with keys as the month and the year of each month for earliest to latest
    var populate_blank_months = month_range.map(function(t){
    if (current_month < 12) {
        months[moment().year(current_year).month(current_month).day("Monday")] = 0
        current_month = parseInt(current_month, 10) + 1
    } else if (current_month == 12) {
        months[moment().year(current_year).month(current_month).day("Monday")] = 0
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

        var week_date = moment().year(year_number).week(week_number).day("Monday")
        var month_date = moment().year(year_number).month(month_number).day("Monday")

        if(typeof aggregate_weeks[week_date] == 'undefined'){
            aggregate_weeks[week_date] = t[1]
        } else {
            for(var i = 0; i < ((t[1]).length); i++) {
                aggregate_weeks[week_date][i] = aggregate_weeks[week_date][i] + t[1][i]
            }
        }
        if(typeof aggregate_months[month_date] == 'undefined'){
            aggregate_months[month_date] = t[1]
        } else {
            for(var i = 0; i < ((t[1]).length); i++) {
                aggregate_months[month_date][i] = aggregate_months[month_date][i] + t[1][i]
            }
        }
    });

    return [weeks, months, aggregate_weeks, aggregate_months]
}

function sortDictByDate(dict){
    sorted_dict = {}
    var sort = (Object.keys(dict)).sort(function(a, b) {
    return new Date(a) - new Date(b);
    });
    var sort_aggregate_weeks = sort.map(function(t){
        sorted_dict[t] = dict[t]
    });
    return sorted_dict
}

function runCharts(yield2date) {

    var date_map = yield2date.map(function(t){
        (t[0]) = (new Date(t[0]))
    });

    var yield2date_aggregate = aggregateData(yield2date)
    var aggregate_weeks = sortDictByDate(yield2date_aggregate[2])
    var aggregate_months = sortDictByDate(yield2date_aggregate[3])

    var by_month_yield_data = []
    var by_week_yield_data = []
    var by_month_yield_data_cumulative = []
    var by_week_yield_data_cumulative = []
    var current_month_cumulative_yield = 0
    var current_week_cumulative_yield = 0

    // format dates and yield for google charts
    // keep running total of values to add to cumulative value

    for (var i in aggregate_weeks) {
        by_week_yield_data.push([new Date(i), aggregate_weeks[i][0]])
        current_week_cumulative_yield += (parseInt(aggregate_weeks[i][0]))
        by_week_yield_data_cumulative.push([new Date(i), current_week_cumulative_yield])
    }
    for (var i in aggregate_months) {
        by_month_yield_data.push([new Date(i), aggregate_months[i][0]])
        current_month_cumulative_yield += (parseInt(aggregate_months[i][0]))
        by_month_yield_data_cumulative.push([new Date(i), current_month_cumulative_yield])
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


    yield_chart.draw(run_yield_data_weeks, run_yield_options_weeks);
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

    var samples_sequenced_aggregate = aggregateData(samples_sequenced)

    var aggregate_weeks = samples_sequenced_aggregate[2]
    var aggregate_months = samples_sequenced_aggregate[3]



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
