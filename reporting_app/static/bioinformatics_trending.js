var chart;
var api_datefmt = 'DD_MM_YYYY_00:00:00';


function depaginate(baseurl, queries, callback) {
    console.log('Depaginating ' + baseurl);

    $.ajax({
        url: build_api_url(baseurl, queries),
        headers: auth_header(),
        dataType: 'json',
        success: function(initial_response) {
            var total_pages = Math.ceil(initial_response._meta.total / initial_response._meta.max_results);
            var data = initial_response.data;
            var calls = _.map(_.range(2, total_pages + 1), function(p) {
                var _queries = JSON.parse(JSON.stringify(queries));  // I love JavaScript.
                _queries['page'] = p;
                return $.ajax({
                    url: build_api_url(baseurl, _queries),
                    headers: auth_header(),
                    dataType: 'json'
                });
            });

            $.when.apply($, calls).then(function() {
                _.forEach(arguments, function(response) {
                    data = data.concat(response[0].data);
                });
                callback(data);
            });
        }
    });
}


function quantise_date_field(date_str) {
    return moment(moment(date_str, api_datefmt).format('YYYY-MM-DD'));
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
    var d = moment(start_date);

    while(d <= end_date) {
        add_entity_at(quantise_date_field(d), targets);
        d = d.add(1, 'days');
    }
}


function build_series(name, entities, start_key, end_key) {
    var entities_by_date = {};
    for (var i=0; i<entities.length; i++) {
        add_entity_running_days(entities[i], entities_by_date, start_key, end_key);
    }

    var data = [];
    for (k in entities_by_date) {
        v = entities_by_date[k];
        data.push([k, v]);
    }

    return {
        name: name,
        data: data
    };
}


function init_bioinformatics_chart() {
    chart = Highcharts.chart('trending_chart', {
        chart: {scrollablePlotArea: {minWidth: 700}},
        title: {text: 'Bioinformatics activity over time'},
        xAxis: {
            type: 'datetime',
            title: {text: 'Date'}
        },
        yAxis: [
            {title: {text: 'n_entities'}},
        ],
        series: []
    });
}


function load_bioinformatics_chart(proc_url, stage_url) {
    chart.showLoading();
    var start_date = moment($('#date_from').val(), 'YYYY-MM-DD');
    var end_date = moment($('#date_to').val(), 'YYYY-MM-DD');

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
        chart.addSeries(build_series('Run procs', split_procs.run, 'start_date', 'end_date'));
        chart.addSeries(build_series('Sample procs', split_procs.sample, 'start_date', 'end_date'));
        chart.addSeries(build_series('Project procs', split_procs.project, 'start_date', 'end_date'));
    });

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
        chart.addSeries(build_series('Run stages', split_stages.run, 'date_started', 'date_finished'));
        chart.addSeries(build_series('Sample stages', split_stages.sample, 'date_started', 'date_finished'));
        chart.addSeries(build_series('Project stages', split_stages.project, 'date_started', 'date_finished'));
    });

    chart.hideLoading();
}