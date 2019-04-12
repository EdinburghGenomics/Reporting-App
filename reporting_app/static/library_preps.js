
var heatmap_x_coords = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];

function get_lims_and_qc_data(lims_url, qc_url, token, time_from, time_to, library_id) {
    var query_args = [];

    if (library_id) {
        query_args.push('library_id=' + library_id);
    } else {
        if (time_from) {
            query_args.push('time_from=' + time_from);
        }
        if (time_to) {
            query_args.push('time_to=' + time_to);
        }
    }

    if (query_args) {
        lims_url = lims_url + '?' + query_args.join('&');
    }

    function merge_qc_data(data) {
        var output_data = [];

        var i;
        var nlibraries = data.length;
        for (i=0; i<nlibraries; i++) {
            var library = data[i];
            var samples = [];
            var placements = library['placements'];

            for (p in placements) {
                var placement = placements[p];
                samples.push('{"sample_id":"' + placement['name'] + '"}');
            }

            var qc_data = {};
            $.ajax(
                {
                    url: qc_url + '?where={"$or":[' + samples.join(',') + ']}&max_results=1000',
                    headers: {'Authorization': token},
                    dataType: 'json',
                    async: false,
                    success: function(result) {
                        var i;
                        var nsamples = result.data.length;
                        for (i=0; i<nsamples; i++) {
                            var sample = result.data[i];
                            qc_data[sample['sample_id']] = sample;
                        }
                    }
                }
            );

            for (p in placements) {
                placements[p]['qc'] = qc_data[placements[p]['name']];
            }
            output_data.push(library);
        }
        return output_data;
    }

    var data;
    $.ajax(
        {
            url: lims_url,
            headers: {'Authorization': token},
            dataType: 'json',
            async: false,
            success: function(result) {
                data = merge_qc_data(result.data);
            }
        }
    );
    return data;
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

function format_library_series(library, colour_field) {
    var series = {
        name: library['id'],
        borderWidth: 1,
        data: [],
        dataLabels: {
            enabled: false,
            color: '#000000'
        }
    }

    var placements = library['placements'];
    for (coord in placements) {
        var split_coord = coord.split(':');
        series['data'].push(
            {
                x: heatmap_x_coords.indexOf(split_coord[0]),
                y: parseInt(split_coord[1]) - 1,
                value: parseFloat(query_nested_object(placements[coord], ['qc', 'aggregated', 'pc_q30'])),
                name: placements[coord]['name']
            }
        );
    }
    return series;
}

function highchart(heatmap_id, library) {
    Highcharts.chart(heatmap_id, {
        chart: {
            type: 'heatmap',
            marginTop: 40,
            marginBottom: 80,
            plotBorderWidth: 1
        },
        title: {text: 'Library ' + library['id']},
        xAxis: {categories: heatmap_x_coords},
        yAxis: {categories: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']},
        colorAxis: {
            min: 0,
            minColor: '#FFFFFF',
            maxColor: Highcharts.getOptions().colors[0]
        },
        legend: {
            align: 'right',
            layout: 'vertical',
            margin: 0,
            verticalAlign: 'top',
            y: 25,
            symbolHeight: 280
        },
        tooltip: {
            formatter: function () {
                return '<p>' + this.point.name + ', ' + this.series.xAxis.categories[this.point.x] + ':' + this.point.y + ', ' + this.point.value + '</p>';
            }
        },
        series: [format_library_series(library, null)]
    });
}
