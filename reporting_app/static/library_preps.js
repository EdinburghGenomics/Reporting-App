
// these are well x coords in the Lims database, but plotted as y coords as per Lims UI
var heatmap_x_coords = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

function get_lims_and_qc_data(lims_url, qc_url, token, library_id) {
    var query_args = [];

    function merge_qc_data_and_plot() {
        var samples = [];
        var sample_coords = {};
        var coords = Object.keys(library_data['qc']);
        for (var j=0; j<coords.length; j++) {
            var coord = coords[j];
            var placement = library_data['qc'][coord];
            sample_coords[placement['name']] = coord;
            samples.push('{"sample_id":"' + placement['name'] + '"}');
        }

        $.ajax(
            {
                url: qc_url + '?where={"$or":[' + samples.join(',') + ']}&max_results=1000',
                headers: {'Authorization': token},
                dataType: 'json',
                success: function(result) {
                    var i;
                    var nsamples = result.data.length;
                    for (i=0; i<nsamples; i++) {
                        var sample = result.data[i];
                        var coord = sample_coords[sample['sample_id']];
                        library_data['qc'][coord]['reporting_app'] = sample;
                    }
                    chart.addSeries(format_series(active_colour_metric));
                    retrigger(active_colour_metric);
                }
            }
        );
    }

    $.ajax(
        {
            url: lims_url + '?library_id=' + library_id,
            headers: {'Authorization': token},
            dataType: 'json',
            success: function(result) {
                library_data = result.data[0];
                merge_qc_data_and_plot();
            }
        }
    );
}

function query_nested_object(top_level, query) {
    var val = top_level;
    for (var i=0; i<query.length; i++) {
        val = val[query[i]];
        if (!val) {
            return null;
        }
    }
    return val;
}

function format_series(colour_metric) {
    var series = {
        name: library_data['id'],
        borderWidth: 1,
        data: [],
        dataLabels: {
            enabled: false,
            color: '#000000'
        }
    }

    var placements = library_data['qc'];
    for (coord in placements) {
        var split_coord = coord.split(':');
        series['data'].push(
            {
                y: heatmap_x_coords.indexOf(split_coord[0]),
                x: parseInt(split_coord[1]) - 1,
                value: parseFloat(parseFloat(query_nested_object(placements[coord], metrics[colour_metric])).toFixed(3)),
                name: placements[coord]['name']
            }
        );
    }
    return series;
}

function highchart(heatmap_id, title) {
    return Highcharts.chart(heatmap_id, {
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
            maxColor: Highcharts.getOptions().colors[0]
        },
        legend: {
            title: {
                text: active_colour_metric
            },
            align: 'right',
            layout: 'vertical',
            margin: 0,
            verticalAlign: 'top',
            y: 25,
            symbolHeight: 280
        },
        tooltip: {
            formatter: function () {
                var coord = this.series.yAxis.categories[this.point.y] + ':' + (this.point.x + 1);
                return '<p>Sample: ' + this.point.name + '<br/>Coord: ' + coord + '<br/>' + active_colour_metric + ': ' + this.point.value + '</p>';
            }
        },
        series: []
    });
}

function retrigger(colour_metric) {
    active_colour_metric = colour_metric;
    chart.series[0].update(format_series(active_colour_metric));
    chart.legend.update(
        {
            title: {
                text: active_colour_metric,
                fontWeight: 'bold'
            }
        }
    );
}