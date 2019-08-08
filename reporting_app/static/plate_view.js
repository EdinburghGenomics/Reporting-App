
var chart, container_data;  // globals for the chart object and the container data to be plotted

// pointer to the current metric being plotted
var active_colour_metric;
var colour_palette = Highcharts.getOptions().colors;

// Artifact y coordinates, but plot them as x coordinates as per Lims UI
var heatmap_y_category;

// Global variable to hold the metrics that can be displayed in this plots
var metrics = {};

function get_lims_and_qc_data(lims_url, qc_url, token, container_id) {
    // query the Lims  endpoint for a single container, set container_data and merge in data from samples endpoint
    $.ajax(
        {
            url: lims_url + '?match={"container_id":"' + container_id + '"}',
            headers: {'Authorization': token},
            dataType: 'json',
            success: function(result) {
                container_data = result.data[0];

                var sample_queries = [];  // sample IDs to merge on
                var sample_coords = {};  // map sample IDs to index of the sample in container_data so we can merge the sequencing qc later
                container_data['samples'].forEach(function(sample, i){
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
                                container_data['samples'][i]['bioinformatics_qc'] = sample_qc;
                            });
                        }
                    }
                );
            }
        }
    );
}

function build_series(colour_metric) {
    // build an object to pass to Highcharts.heatmap.series, converting container QC data into an array of data points
    var series = {
        name: container_data[0]['id'],
        data: [],
        dataLabels: {enabled: false}
    }

    _.forEach(container_data, function(sample){
        var split_coord = sample['location'].split(':');
        series.data.push(
            {
                y: heatmap_y_category.indexOf(split_coord[0]),
                x: parseInt(split_coord[1]) - 1,
                value: _.get(sample, metrics[colour_metric]['data']) || '(missing value)',
                name: sample['name']
            }
        );
    });
    return series;
}

function init_heatmap(div_id, container_id, lims_url, qc_url, ajax_token, view_metrics, plate_type) {
    // Assign the metrics and create a button for each metric
    _.forEach(view_metrics, function(m) {
        var li = $('#button_' + m.name);
        var button = $('<a>').attr('target', m.name).text(m.title);
        button.click(function() { render_heatmap(this.target); $('#selected_metric').text(this.text); });
        li.append(button);
        metrics[m.name]=m
    });

    // Select the type of plate layout (default to 96 well plate)
    // heatmap_y_category is a global variable because it need to be accessed
    var heatmap_x_category;
    if (plate_type && plate_type == '384'){
        heatmap_x_category =  _.range(1, 25).map(function(a){ return a.toString()})
        heatmap_y_category = 'ABCDEFGHIJKLMNOP'.split('')
    }else{
        heatmap_x_category = _.range(1, 13).map(function(a){ return a.toString()})
        heatmap_y_category = 'ABCDEFGH'.split('')
    }

    chart = Highcharts.chart(div_id, {
        chart: {
            type: 'heatmap',
            marginTop: 40,
            marginBottom: 80,
            plotBorderWidth: 1,
            height: '50%'
        },
        title: { text: 'Container ' + container_id },
        yAxis: { categories: heatmap_y_category, min: 0, max: heatmap_y_category.length - 1, reversed: true, title: null },
        xAxis: { categories: heatmap_x_category, min: 0, max: heatmap_x_category.length - 1 },
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
}


function load_data_to_chart(dt_settings, json){
    // function to transfer the data from the associated datatables after it finished loading
    container_data = json.data;
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
