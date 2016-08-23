



function aggregateData(data) {

      var all_month_year = []
      var all_week_year = []
      date_array = []

      var test_map = data.map(function(t){
             var week_year = []
             var month_year = []
             var date = moment(new Date(t[0]))
             week = date.format('W')
             month = date.format('M')
             year = date.format('Y')
             var v = [week, year]
             date_array.push(date)
      });

      min_date = moment.min(date_array)
      max_date = moment.max(date_array)
      min_week = min_date.format('W')
      min_month = min_date.format('M')
      min_year = min_date.format('Y')
      var number_of_weeks = max_date.diff(min_date, 'weeks') + 1
      var number_of_months = max_date.diff(min_date, 'months') + 1
      var week_range = Array.apply(null, {length: number_of_weeks}).map(Number.call, Number)
      var month_range = Array.apply(null, {length: number_of_months}).map(Number.call, Number)
      var weeks = {}
      var months = {}

      current_week = min_week
      current_year = min_year

      var populate_blank_weeks = week_range.map(function(t){
            if (current_week < 52) {
                  weeks[([parseInt(current_week), parseInt(current_year)])] = 0
                  current_week = parseInt(current_week, 10) + 1

            } else if (current_week == 52) {
                  weeks[([parseInt(current_week), parseInt(current_year)])] = 0
                  current_week = 1
                  current_year = parseInt(current_year, 10) + 1
            }
      });

      current_month = min_month
      current_year = min_year


      var populate_blank_months = month_range.map(function(t){
            if (current_month < 12) {
                  months[([parseInt(current_month), parseInt(current_year)])] = 0
                  current_month = parseInt(current_month, 10) + 1

            } else if (current_month == 12) {
                  months[([parseInt(current_month), parseInt(current_year)])] = 0
                  current_month = 1
                  current_year = parseInt(current_year, 10) + 1
            }
      });


      var aggregate_weeks = {}
      var aggregate_months = {}

      var available_dates = data.map(function(t){
            week_number = moment(new Date(t[0])).week()
            month_number = (moment(new Date(t[0])).month()) + 1
            year_number = moment(new Date(t[0])).year()

            var month_year = [month_number, year_number]
            var week_year = [week_number, year_number]

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

    var histogram_data = google.visualization.arrayToDataTable(hist);
    yield2date_aggregate = aggregateData(yield2date)

    weeks = yield2date_aggregate[0]
    months = yield2date_aggregate[1]
    aggregate_weeks = yield2date_aggregate[2]
    aggregate_months = yield2date_aggregate[3]

    by_month_yield_data = []
    by_week_yield_data = []
    by_month_yield_data_cumulative = []
    by_week_yield_data_cumulative = []
    current_month_yield = 0
    current_week_cummulative_yield = 0

    // Create cumulative and fill in blanks with zeros
    for (var week in weeks) {
        if( week in aggregate_weeks) {
            current_week_cummulative_yield += (parseInt(aggregate_weeks[week]))
            by_week_yield_data.push([week, aggregate_weeks[week]])
            by_week_yield_data_cumulative.push([week, current_week_cummulative_yield])
        } else {
            by_week_yield_data.push([week, 0])
            by_week_yield_data_cumulative.push([week, current_week_cummulative_yield])
        }
    }

    for (var key in months) {
        if(typeof aggregate_months[key] != 'undefined') {
              current_month_yield = current_month_yield += parseInt(aggregate_months[key])
              by_month_yield_data.push([key, aggregate_months[key][0]])
              by_month_yield_data_cumulative.push([key, current_month_yield])
        } else if(typeof aggregate_months[key] == 'undefined') {
              current_month_yield = current_month_yield += parseInt(months[key])
              by_month_yield_data.push([key, months[key]])
              by_month_yield_data_cumulative.push([key, current_month_yield])
        }
    }


    var run_yield_data = new google.visualization.DataTable();
    run_yield_data.addColumn('string', 'X');
    run_yield_data.addColumn('number', 'Yield');
    run_yield_data.addRows(by_month_yield_data);
    var run_yield_options = {
    hAxis: {title: 'Date'},
    vAxis: {title: 'Yield'}};
    var yield_chart = new google.visualization.ColumnChart(document.getElementById('run_yield_by_date'));
    yield_chart.draw(run_yield_data, run_yield_options);


    var cumulative_run_yield_data = new google.visualization.DataTable();
    cumulative_run_yield_data.addColumn('string', 'X');
    cumulative_run_yield_data.addColumn('number', 'Yield');
    cumulative_run_yield_data.addRows(by_month_yield_data_cumulative);
    var cumulative_run_yield_options = {
    hAxis: {title: 'Date'},
    vAxis: {title: 'Cumulative Yield'}};
    var cumulative_yield_chart = new google.visualization.LineChart(document.getElementById('cumulative_run_yield_by_date'));
    cumulative_yield_chart.draw(cumulative_run_yield_data, cumulative_run_yield_options);


    var histogram_options = {
    title: 'Yield metrics',
    legend: { position: 'top', maxLines: 2 },
    colors: ['#1A8763', '#5C3292'],
    interpolateNulls: false};
    var yield_histogram = new google.visualization.Histogram(document.getElementById('yield_histogram'));
    yield_histogram.draw(histogram_data, histogram_options);


}



function sampleCharts(samples_sequenced, hist) {

    samples_sequenced_aggregate = aggregateData(samples_sequenced)

    weeks = samples_sequenced_aggregate[0]
    months = samples_sequenced_aggregate[1]
    aggregate_weeks = samples_sequenced_aggregate[2]
    aggregate_months = samples_sequenced_aggregate[3]

    by_month_samples_data = []
    by_week_samples_data = []


    for (var key in weeks) {
        if(typeof aggregate_weeks[key] != 'undefined') {
              by_week_samples_data.push([key, aggregate_weeks[key][0], aggregate_weeks[key][1], aggregate_weeks[key][2]])
        } else if(typeof aggregate_weeks[key] == 'undefined') {
              by_week_samples_data.push([key, weeks[key], weeks[key], weeks[key]])
        }
    }

    for (var key in months) {
        if(typeof aggregate_months[key] != 'undefined') {
              by_month_samples_data.push([key, aggregate_months[key][0], aggregate_months[key][1], aggregate_months[key][2]])
        } else if(typeof aggregate_months[key] == 'undefined') {
              by_month_samples_data.push([key, months[key], months[key], months[key]])
        }
    }

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


    var chart3 = new google.visualization.LineChart(document.getElementById('samples_sequenced'));
    var sample_options = {
    hAxis: {title: 'Date'},
    vAxis: {title: 'Number of Samples'}};

    chart3.draw(sample_data_month, sample_options);

    var show_months = document.getElementById("ShowMonths");
    show_months.onclick = function()
    {
     view = new google.visualization.DataView(sample_data_month);
     chart3.draw(sample_data_month, sample_options);
    }
    var show_weeks = document.getElementById("ShowWeeks");
    show_weeks.onclick = function()
    {
     view = new google.visualization.DataView(sample_data_week);
     chart3.draw(sample_data_week, sample_options);
    }



    var histogram_data = google.visualization.arrayToDataTable(hist);
    var histogram_options = {
    title: 'Yield metrics',
    legend: { position: 'top', maxLines: 2 },
    colors: ['#1A8763', '#5C3292'],
    interpolateNulls: false};
    var chart2 = new google.visualization.Histogram(document.getElementById('yield_histogram'));
    chart2.draw(histogram_data, histogram_options);


}





