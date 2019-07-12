
var chart, library_data;  // globals for the chart object and the library data to be plotted

// pointer to the current metric being plotted
var active_colour_metric;
var colour_palette = Highcharts.getOptions().colors;

// Artifact y coordinates, but plot them as x coordinates as per Lims UI
var heatmap_x_coords = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

metrics = {
    'pc_q30': {name: '%Q30', path: ['bioinformatics_qc', 'aggregated', 'pc_q30']},
    'pc_mapped_reads': {name: '% mapped reads', path: ['bioinformatics_qc', 'aggregated', 'pc_mapped_reads']},
    'species': {name: 'Species', path: ['bioinformatics_qc', 'species_name'], type: 'category'},
    'matching_species': {name: 'Matching species', path: ['bioinformatics_qc', 'aggregated', 'matching_species'], type: 'category'},
    'het_hom_ratio': {name: 'Het/hom ratio', path: ['bioinformatics_qc', 'sample_contamination', 'het_hom_ratio']},
    'freemix': {name: 'Freemix', path: ['bioinformatics_qc', 'sample_contamination', 'freemix']},
    'genotype_match': {name: 'Genotype match', path: ['bioinformatics_qc', 'aggregated', 'genotype_match'], type: 'category'},
    'pc_optical_duplicates': {name: '% optical duplicates', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'pc_opt_duplicate_reads']},
    'pc_duplicates': {name: '% duplicates', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'pc_duplicate_reads']},
    'gc_bias_mean_dev': {name: 'GC bias (mean deviation)', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'gc_bias', 'mean_deviation']},
    'gc_bias_slope': {name: 'GC bias (slope)', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'gc_bias', 'slope']},
    'pc_adaptor': {name: '% adaptor', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'pc_adaptor']},
    'mean_insert_size': {name: 'Mean insert size', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'mean_insert_size']},
    'library_size': {name: 'Picard est. lib size', path: ['bioinformatics_qc', 'aggregated', 'from_all_run_elements', 'picard_est_lib_size']},
    'av_conc': {name: 'Ave. Conc. (nM)', path: ['udfs', 'Ave. Conc. (nM)']},
    'pc_cv': {name: '%CV', path: ['udfs', '%CV']},
    'raw_cp': {name: 'Raw CP', path: ['udfs', 'Raw CP']},
    'ntp_volume': {name: 'NTP Volume (uL)', path: ['udfs', 'NTP Volume (uL)']},
    'adjusted_conc': {name: 'Adjusted Conc. (nM)', path: ['udfs', 'Adjusted Conc. (nM)']},
    'original_conc': {name: 'Original Conc. (nM)', path: ['udfs', 'Original Conc. (nM)']},
    'ntp_transfer_vol': {name: 'NTP Transfer Volume (uL)', path: ['udfs', 'NTP Transfer Volume (uL)']},
    'rsb_transfer_vol': {name: 'RSB Transfer Volume (uL)', path: ['udfs', 'RSB Transfer Volume (uL)']},
    'sample_transfer_vol': {name: 'Sample Transfer Volume (uL)', path: ['udfs', 'Sample Transfer Volume (uL)']},
    'tsp1_transfer_vol': {name: 'TSP1 Transfer Volume (uL)', path: ['udfs', 'TSP1 Transfer Volume (uL)']},
    'qc_flag': {name: 'QC flag', path: ['qc_flag'], type: 'category'},
    'project_id': {name: 'Project ID', path: ['project_id'], type: 'category'}
};


function get_lims_and_qc_data(lims_url, qc_url, token, library_id) {
    // query the Lims library_info endpoint for a single library, set library_data and merge in data from samples endpoint
    $.ajax(
        {
            url: lims_url + '?match={"container_id":"' + library_id + '"}',
            headers: {'Authorization': token},
            dataType: 'json',
            success: function(result) {
                library_data = result.data[0];

                var sample_queries = [];  // sample IDs to merge on
                var sample_coords = {};  // map sample IDs to index of the sample in library_data so we can merge the sequencing qc later
                library_data['samples'].forEach(function(sample, i){
                    var sample_id = sample['name'];
                    sample_coords[sample_id] = i;
                    sample_queries.push('{"sample_id":"' + sample_id + '"}');
                });
                // query the samples endpoint for IDs found above, merge in the data and trigger the chart
                $.ajax(
                    {
                        url: qc_url + '?where={"$or":[' + sample_queries.join(',') + ']}&max_results=1000',
                        headers: {'Authorization': token},
                        dataType: 'json',
                        success: function(result) {
                            _.forEach(result.data, function(sample_qc) {
                                var i = sample_coords[sample_qc['sample_id']];
                                library_data['samples'][i]['bioinformatics_qc'] = sample_qc;
                            });
                        }
                    }
                );
            }
        }
    );
}

function build_series(colour_metric) {
    // build an object to pass to Highcharts.heatmap.series, converting library QC data into an array of data points
    var series = {
        name: library_data['id'],
        data: [],
        dataLabels: {enabled: false}
    }

    _.forEach(library_data['samples'], function(sample){
        var split_coord = sample['location'].split(':');
        console.log(split_coord);
        series.data.push(
            {
                y: heatmap_x_coords.indexOf(split_coord[0]),
                x: parseInt(split_coord[1]) - 1,
                value: _.get(sample, metrics[colour_metric]['path']) || '(missing value)',
                name: sample['name']
            }
        );
    });
    console.log(series)
    return series;
}

function init_heatmap(div_id, library_id, lims_url, qc_url, ajax_token) {
    chart = Highcharts.chart(div_id, {
        chart: {
            type: 'heatmap',
            marginTop: 40,
            marginBottom: 80,
            plotBorderWidth: 1,
            height: '50%'
        },
        title: {text: 'Library ' + library_id},
        yAxis: {categories: heatmap_x_coords, min: 0, max: 7, reversed: true, title: null},
        xAxis: {categories: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'], min: 0, max: 11},
        colorAxis: {
            minColor: '#FFFFFF',
            maxColor: colour_palette[0]
        },
        legend: {
            align: 'right',
            layout: 'vertical',
            margin: 0,
            verticalAlign: 'top',
            y: 25
        },
        tooltip: {
            formatter: function () {
                var coord = this.series.yAxis.categories[this.point.y] + ':' + (this.point.x + 1);
                return '<p>Sample: ' + this.point.name + '<br/>Coord: ' + coord + '<br/>' + metrics[active_colour_metric]['name'] + ': ' + this.point.label + '</p>';
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

function render_heatmap(colour_metric) {
    /*
    Reset the active_colour_metric, decide how to build the new data series, update the chart with the new series, and
    update the chart legend with the new metric name.
    */

    active_colour_metric = colour_metric;

    var transform_func;
    var series = build_series(colour_metric);

    if (metrics[colour_metric]['type'] == 'category') {
        categories = _.uniq(
            _.map(
                series.data,
                function(data_point) {
                    var datatype = typeof data_point.value;
                    if (datatype == 'object') {
                        data_point.value = data_point.value.sort().join(', ');
                    }
                    return data_point.value;
                }
            )
        );

        chart.colorAxis[0].update({dataClasses: data_classes(categories)});
        transform_func = function(data_point) {
            // value must be a number, but show the category name in chart.tooltip
            data_point.value = categories.indexOf(data_point.value);
            data_point.label = categories[data_point.value];
        }
    } else {
        chart.colorAxis[0].update({dataClasses: null});
        transform_func = function(data_point) {
            // default: plot as a float rounded to 3 decimal places
            data_point.value = parseFloat(parseFloat(data_point.value).toFixed(3));
            data_point.label = data_point.value;
        }
    }

    _.forEach(series.data, function(data_point) { transform_func(data_point); });

    _.forEach(chart.series, function(series) { series.remove(); });
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
