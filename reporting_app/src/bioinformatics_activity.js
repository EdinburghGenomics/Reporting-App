import _ from 'lodash';
import $ from 'jquery';
import moment from 'moment';
import Highcharts from 'highcharts';
import { depaginate } from './utils.js'


var api_datefmt = 'DD_MM_YYYY_00:00:00';  // parse API timestamps as 00:00:00 that day


export function add_entity_running_days(entity, entities_by_date, started_str, finished_str) {
    /*
    Find all the days a process was running, and increment all of those days by 1 in entities_by_date, e.g:
    var entities_by_date = {day_1: 0, day_2, 0, day_3: 0};
    add_entity_running_days({start: 'day_1', end: 'day_2'}, entities_by_date, 'start', 'end');
    -> entities_by_date should now be {day_1: 1, day_2: 1, day_3: 0}
    */

    var start_date = moment.utc(entity[started_str], api_datefmt);
    var end_date = moment.utc(entity[finished_str], api_datefmt);
    var m = moment.utc(start_date);

    while(m <= end_date) {
        entities_by_date[m.valueOf()] += 1;
        m = m.add(1, 'days');
    }
}


export function build_bioinf_series(name, entities, start_key, end_key, start, end) {
    // initialise series as {day_1: 0, day_2: 0, day_3: 0, ...} between start and end
    var entities_by_date = {};
    var m = moment.utc(start);
    while (m <= end) {
        entities_by_date[m.valueOf()] = 0;
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
    window.chart = Highcharts.chart('activity_chart', {
        chart: {scrollablePlotArea: {minWidth: 700}},
        title: {text: 'Bioinformatics pipeline activity'},
        xAxis: {type: 'datetime', title: {text: 'Date'}},
        yAxis: [{title: {text: 'n_entities'}}],
        series: []
    });

    $('#submit').click(function() {
        load_bioinformatics_chart();
    });
}


function load_bioinformatics_chart() {
    chart.showLoading();

    var start_date = moment.utc($('#date_from').val(), 'YYYY-MM-DD');
    var end_date = moment.utc($('#date_to').val(), 'YYYY-MM-DD');
    var include_stages = $('#include_stages').prop('checked');

    // Clear the chart first. Removing multiple series means we need to iterate in reverse.
    _.forEachRight(chart.series, function(series) { series.remove(); });

    var proc_filter = JSON.stringify({
        'start_date': {'$gt': start_date.format(api_datefmt)},
        'end_date': {'$lt': end_date.format(api_datefmt)}
    });
    depaginate('analysis_driver_procs', {where: proc_filter, max_results: 1000}, function(all_procs) {
        var split_procs = {
            'run': [],
            'sample': [],
            'project': []
        }
        _.forEach(all_procs, function(proc) {
            // e.g, {dataset_type: 'run'} gets pushed to split_procs.run
            split_procs[proc.dataset_type].push(proc);
        });
        chart.addSeries(build_bioinf_series('Run procs', split_procs.run, 'start_date', 'end_date', start_date, end_date));
        chart.addSeries(build_bioinf_series('Sample procs', split_procs.sample, 'start_date', 'end_date', start_date, end_date));
        chart.addSeries(build_bioinf_series('Project procs', split_procs.project, 'start_date', 'end_date', start_date, end_date));
    });

    if (include_stages) {
        var stage_filter = JSON.stringify({
            'date_started': {'$gt': start_date.format(api_datefmt)},
            'date_finished': {'$lt': end_date.format(api_datefmt)}
        });
        depaginate('analysis_driver_stages', {where: stage_filter, max_results: 1000}, function(all_stages) {
            var split_stages = {
                'run': [],
                'sample': [],
                'project': []
            }
            _.forEach(all_stages, function(stage) {
                // e.g, {stage_id: 'run_x_stage_1'} gets pushed to split_stages.run
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
