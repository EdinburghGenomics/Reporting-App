
var chart, library_data;  // globals for the chart object and the library data to be plotted

// pointer to the current metric being plotted
var active_colour_metric = 'pc_q30';
var colour_palette = Highcharts.getOptions().colors;

// Artifact y coordinates, but plot them as x coordinates as per Lims UI
var heatmap_x_coords = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

metrics = {
    'pc_q30': {name: '%Q30', path: ['reporting_app', 'aggregated', 'pc_q30']},
    'pc_mapped_reads': {name: '% mapped reads', path: ['reporting_app', 'aggregated', 'pc_mapped_reads']},
    'av_conc': {name: 'Ave. Conc. (nM)', path: ['udf', 'Ave. Conc. (nM)']},
    'pc_cv': {name: '%CV', path: ['udf', '%CV']},
    'raw_cp': {name: 'Raw CP', path: ['udf', 'Raw CP']},
    'ntp_volume': {name: 'NTP Volume (uL)', path: ['udf', 'NTP Volume (uL)']},
    'adjusted_conc': {name: 'Adjusted Conc. (nM)', path: ['udf', 'Adjusted Conc. (nM)']},
    'original_conc': {name: 'Original Conc. (nM)', path: ['udf', 'Original Conc. (nM)']},
    'ntp_transfer_vol': {name: 'NTP Transfer Volume (uL)', path: ['udf', 'NTP Transfer Volume (uL)']},
    'rsb_transfer_vol': {name: 'RSB Transfer Volume (uL)', path: ['udf', 'RSB Transfer Volume (uL)']},
    'sample_transfer_vol': {name: 'Sample Transfer Volume (uL)', path: ['udf', 'Sample Transfer Volume (uL)']},
    'tsp1_transfer_vol': {name: 'TSP1 Transfer Volume (uL)', path: ['udf', 'TSP1 Transfer Volume (uL)']},
    'qc_flag': {name: 'QC flag', path: ['qc_flag'], categories: ['UNKNOWN', 'PASSED', 'FAILED', 'ERRORED']}
};


function get_lims_and_qc_data(lims_url, qc_url, token, library_id) {
    // query the Lims library_info endpoint for a single library, set library_data and merge in data from samples endpoint
    $.ajax(
        {
            url: lims_url + '?match={"library_id":"' + library_id + '"}',
            headers: {'Authorization': token},
            dataType: 'json',
            success: function(result) {
                library_data = result.data[0];

                var sample_queries = [];  // sample IDs to merge on
                var sample_coords = {};  // map sample IDs to well coordinates so we know where to merge the data

                var coords = Object.keys(library_data['qc']);
                for (var i=0; i<coords.length; i++) {
                    var coord = coords[i];
                    var placement = library_data['qc'][coord];
                    var sample_id = placement['name'];
                    sample_coords[sample_id] = coord;
                    sample_queries.push('{"sample_id":"' + sample_id + '"}');
                }

                // query the samples endpoint for IDs found above, merge in the data and trigger the chart
                $.ajax(
                    {
                        url: qc_url + '?where={"$or":[' + sample_queries.join(',') + ']}&max_results=1000',
                        headers: {'Authorization': token},
                        dataType: 'json',
                        success: function(result) {
                            var j;
                            var nsamples = result.data.length;
                            for (j=0; j<nsamples; j++) {
                                var sample = result.data[j];
                                var coord = sample_coords[sample['sample_id']];
                                library_data['qc'][coord]['reporting_app'] = sample;
                            }
                            trigger(active_colour_metric);
                        }
                    }
                );
            }
        }
    );
}

function query_nested_object(top_level, query) {
    // e.g, query_nested_object({'x': {'y': 'z'}}, ['x', 'y']) -> 'z'
    var val = top_level;
    for (var i=0; i<query.length; i++) {
        val = val[query[i]];
        if (!val) {
            return null;
        }
    }
    return val;
}

function build_series(colour_metric, format_func) {
    // build an object to pass to Highcharts.heatmap.series, converting library QC data into an array of data points
    var series = {
        name: library_data['id'],
        data: [],
        dataLabels: {enabled: false}
    }

    var placements = library_data['qc'];
    for (coord in placements) {
        var split_coord = coord.split(':');
        series.data.push(
            {
                y: heatmap_x_coords.indexOf(split_coord[0]),
                x: parseInt(split_coord[1]) - 1,
                value: format_func(query_nested_object(placements[coord], metrics[colour_metric]['path'])),
                name: placements[coord]['name']
            }
        );
    }
    return series;
}

function highchart(heatmap_id, title, lims_url, qc_url, ajax_token, library_id) {
    chart = Highcharts.chart(heatmap_id, {
        chart: {
            type: 'heatmap',
            marginTop: 40,
            marginBottom: 80,
            plotBorderWidth: 1,
            width: 800,
            height: 400
        },
        title: {text: 'Library ' + title},
        yAxis: {categories: heatmap_x_coords, max: 7, reversed: true, title: null},
        xAxis: {categories: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], max: 11},
        colorAxis: {
            minColor: '#FFFFFF',
            maxColor: colour_palette[0]
        },
        legend: {
            title: {
                text: metrics[active_colour_metric]['name']
            },
            align: 'right',
            layout: 'vertical',
            margin: 0,
            verticalAlign: 'top',
            y: 25
        },
        tooltip: {
            formatter: function () {
                var coord = this.series.yAxis.categories[this.point.y] + ':' + (this.point.x + 1);
                return '<p>Sample: ' + this.point.name + '<br/>Coord: ' + coord + '<br/>' + metrics[active_colour_metric]['name'] + ': ' + this.point.value + '</p>';
            }
        },
        series: []
    });
    chart.showLoading();
    get_lims_and_qc_data(lims_url, qc_url, ajax_token, library_id);
    chart.hideLoading();
}

function data_classes(categories) {
    // Map a list of category names into a list of dataClasses to pass to Highcharts.heatmap.colorAxis.dataClasses
    var data_classes = [];
    for (var i=0; i<categories.length; i++) {
        data_classes.push(
            {
                from: i,
                to: i + 1,
                color: colour_palette[i],
                name: categories[i]
            }
        );
    }
    return data_classes;
}

function trigger(colour_metric) {
    /*
    Reset the active_colour_metric, decide how to build the new data series, update the chart with the new series, and
    update the chart legend with the new metric name.
    */

    active_colour_metric = colour_metric;

    var format_func;
    var metric_config = metrics[colour_metric];

    if (metric_config.hasOwnProperty('categories')) {
        chart.colorAxis[0].update({dataClasses: data_classes(metric_config['categories'])});
        format_func = function(data_point) {
            return metrics[colour_metric]['categories'].indexOf(data_point);  // data point value must be a number
        }
    } else {
        chart.colorAxis[0].update({dataClasses: null});
        format_func = function(data_point) {
            return parseFloat(parseFloat(data_point).toFixed(3));  // default: plot as a float rounded to 3 decimal places
        }
    }

    var series = build_series(colour_metric, format_func);
    for (var i=0; i<chart.series.length; i++) {
        chart.series[i].remove();
    }
    chart.addSeries(series);

    chart.legend.update(
        {
            title: {
                text: metrics[active_colour_metric]['name'],
                fontWeight: 'bold'
            }
        }
    );
}
