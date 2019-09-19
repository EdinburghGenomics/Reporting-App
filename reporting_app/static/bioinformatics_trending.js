var chart;
var api_datefmt = 'DD_MM_YYYY_00:00:00';


function depaginate(baseurl, queries, callback) {
    $.ajax({
        url: build_api_url(baseurl, queries),
        headers: auth_header(),
        dataType: 'json',
        success: function(initial_response) {
            var total_pages = Math.ceil(initial_response._meta.total / initial_response._meta.max_results);
            var data = initial_response.data;

            if (total_pages < 2) {  // no data, or only 1 page - no depagination needed
                callback(data);
            } else {
                console.log('Depaginating ' + total_pages + ' pages from ' + baseurl + ', ' + JSON.stringify(queries));
                var extra_pages = total_pages - 1;

                if (extra_pages == 1) {  // only page 2 to get
                    var _queries = JSON.parse(JSON.stringify(queries));
                    _queries['page'] = 2;
                    $.ajax({
                        url: build_api_url(baseurl, _queries),
                        headers: auth_header(),
                        dataType: 'json',
                        success: function(response) {
                            // we already know the request was successful, so reponse is just the response text
                            data = data.concat(response.data);
                            callback(data);
                        }
                    });
                } else {  // >2 more pages to get - pass through $.when
                    var calls = _.map(_.range(2, total_pages + 1), function(p) {
                        var _queries = JSON.parse(JSON.stringify(queries));
                        _queries['page'] = p;
                        return $.ajax({
                            url: build_api_url(baseurl, _queries),
                            headers: auth_header(),
                            dataType: 'json'
                        });
                    });
                    $.when.apply($, calls).then(function() {
                        _.forEach(arguments, function(response) {
                            // dealing with deferred requests, which could be successful or not, so response is an
                            // object of response text, status and response object
                            data = data.concat(response[0].data);
                        });
                        callback(data);
                    });
                }
            }
        }
    });
}


function quantise_moment(m) {
    return moment(m.format('YYYY-MM-DD'));
}


function add_entity_at(date, targets) {
    if (targets[date]) {
        targets[date] += 1;
    } else {
        targets[date] = 1;
    }
}


function add_entity_running_days(entity, targets, started_str, finished_str) {
    var start_date = moment(entity[started_str], api_datefmt);
    var end_date = moment(entity[finished_str], api_datefmt);
    var m = moment(start_date);

    while(m <= end_date) {
        add_entity_at(quantise_moment(m).valueOf(), targets);
        m = m.add(1, 'days');
    }
}


function build_bioinf_series(name, entities, start_key, end_key, start, end) {
    var entities_by_date = {};
    var m = moment(start);
    while (m <= end) {
        entities_by_date[quantise_moment(m).valueOf()] = 0;
        m = m.add(1, 'days');
    }

    _.forEach(entities, function(e) {
        add_entity_running_days(e, entities_by_date, start_key, end_key);
    });

    var data = _.map(entities_by_date, function(v, k) { return [parseInt(k), v]; });
    data.sort(function(a, b) { return a[0] - b[0];});  // Highcharts expects data to be in order

    return {
        name: name,
        data: data
    };
}


function init_bioinformatics_chart() {
    chart = Highcharts.chart('trending_chart', {
        chart: {scrollablePlotArea: {minWidth: 700}},
        title: {text: 'Bioinformatics activity over time'},
        xAxis: {type: 'datetime', title: {text: 'Date'}},
        yAxis: [{title: {text: 'n_entities'}}],
        series: []
    });
}


function load_bioinformatics_chart(proc_url, stage_url) {
    chart.showLoading();
    var start_date = moment($('#date_from').val(), 'YYYY-MM-DD');
    var end_date = moment($('#date_to').val(), 'YYYY-MM-DD');
    var include_stages = $('#include_stages').prop('checked');

    var proc_filter = '{"start_date":{"$gt":"' + start_date.format(api_datefmt) + '"},"end_date":{"$lt":"' + end_date.format(api_datefmt) + '"}}';
    var stage_filter = '{"date_started":{"$gt":"' + start_date.format(api_datefmt) + '"},"date_finished":{"$lt":"' + end_date.format(api_datefmt) + '"}}';

    _.forEach(chart.series, function(series) { series.remove(); });

    depaginate(proc_url, {where: proc_filter, max_results: 1000}, function(all_procs) {
        var split_procs = {
            'run': [],
            'sample': [],
            'project': []
        }
        _.forEach(all_procs, function(proc) {
            split_procs[proc.dataset_type].push(proc);
        });
        chart.addSeries(build_bioinf_series('Run procs', split_procs.run, 'start_date', 'end_date', start_date, end_date));
        chart.addSeries(build_bioinf_series('Sample procs', split_procs.sample, 'start_date', 'end_date', start_date, end_date));
        chart.addSeries(build_bioinf_series('Project procs', split_procs.project, 'start_date', 'end_date', start_date, end_date));
    });

    if (include_stages) {
        depaginate(stage_url, {where: stage_filter, max_results: 1000}, function(all_stages) {
            var split_stages = {
                'run': [],
                'sample': [],
                'project': []
            }
            _.forEach(all_stages, function(stage) {
                var stage_type = stage['stage_id'].split('_')[0];
                split_stages[stage_type].push(stage);
            });
            chart.addSeries(build_bioinf_series('Run stages', split_stages.run, 'date_started', 'date_finished', start_date, end_date));
            chart.addSeries(build_bioinf_series('Sample stages', split_stages.sample, 'date_started', 'date_finished', start_date, end_date));
            chart.addSeries(build_bioinf_series('Project stages', split_stages.project, 'date_started', 'date_finished', start_date, end_date));
        });
    }

    chart.hideLoading();
}