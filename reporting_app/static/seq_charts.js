
var colour_palette = Highcharts.getOptions().colors;

// Global variables
var chart;
var lane_data;
var lane_metrics = {};
var color_options = {};
var plot_options = {
    'scatter': {'name': 'scatter', 'title': 'Scatter plot', 'function': scatter_series},
    'scatter_smooth': {'name': 'scatter_smooth', 'title': 'Scatter plot with smooth line', 'function': scatter_series_with_smooth_line},
    'box': {'name': 'box', 'title': 'Box plot', 'function': box_plot_series},
    'average': {'name': 'average', 'title': 'Line plot of average', 'function': average_series},
    'average_smooth': {'name': 'average_smooth', 'title': 'plot of average with smooth line', 'function': average_series_with_smooth_line},
}

// Get the unique value from a list of object and
function get_categories(data, key){
    var categories = _.uniq(extract(data, key))
    categories.sort()
    return categories
}

function box_plot_series(data, color_key, metric_path, metric_name){
    // Generate a box plot with outliers series  based on the provided color key and metric
    var series = []
    var i = 0;

    var color_categories = get_categories(data, color_key)
    // calculate the optimal number of decimal point to display
    var nb_decimal = significant_figures(extract(data, metric_path))

    color_categories.map(function(category){
        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        var aggregated_data = aggregate(filtered_data, 'date', metric_path, boxplot_values_outliers, 'metric_box', [0])

        var outliers = aggregated_data.map(function(d){return d.metric_box.outliers.map(function(o){return [parseInt(d['date']), o]}); });
        outliers = [].concat.apply([], outliers);
        values = aggregated_data.map(function(d){return [parseInt(d['date'])].concat(d.metric_box.values)})

        series.push({
            name: category,
            data: aggregated_data.map(function(d){return [parseInt(d['date'])].concat(d.metric_box.values)}),
            yAxis: 0,
            type: 'boxplot',
            tooltip: {
                pointFormatter: function(){return format_boxplot_tooltip(color_key + " " + category, this.x, this.options, 'date', metric_name, '', nb_decimal);}
            },
            color: colour_palette[i],
        })
        series.push({
            name: category,
            data: outliers,
            yAxis: 0,
            type: 'scatter',
            linkedTo: ':previous',
            marker: {
                enabled: true,
                radius: 2,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_point_tooltip(color_key + " " + category, this.x, this.y, 'date', metric_name, '', nb_decimal);}
            },
            color: colour_palette[i],
        })
        i += 1;
    })
    return series
}

function scatter_series(data, color_key, metric_path, metric_name){
    return _scatter_series(data, color_key, metric_path, metric_name, false)
}

function scatter_series_with_smooth_line(data, color_key, metric_path, metric_name){
    return _scatter_series(data, color_key, metric_path, metric_name, true)
}

function _scatter_series(data, color_key, metric_path, metric_name, smooth_line){
    // Generate a plot with scatter series based on the provided color key and metric
    // No aggregation is performed
    var color_categories = get_categories(data, color_key)
    var nb_decimal = significant_figures(extract(data, metric_path))

    var i = 0;

    return color_categories.map(function(category){
        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        series = {
            name: category,
            data: _.map(filtered_data, function(d){return {x: parseInt(d['date']), y:_.get(d, metric_path), name: _.get(d, 'lane_id')} }),
            yAxis: 0,
            type: 'scatter',
            marker: {
                enabled: true,
                radius: 5,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_point_tooltip(this.name, this.x, this.y, 'date', metric_name, '', nb_decimal);}
            },
            color: colour_palette[i]
        }
        if (smooth_line){
            series.regression = true
            series.regressionSettings = { type: 'loess', loessSmooth: 50, color: colour_palette[i], name: "smooth " + category }
        }
        i += 1;
        return series
    })
}

function average_series(data, color_key, metric_path, metric_name){
    return _average_series(data, color_key, metric_path, metric_name, false)
}

function average_series_with_smooth_line(data, color_key, metric_path, metric_name){
    return _average_series(data, color_key, metric_path, metric_name, true)
}

function _average_series(data, color_key, metric_path, metric_name, smooth_line){
    // Generate a plot series showing average of the provided color key and metric
    var color_categories = get_categories(data, color_key)
    var nb_decimal = significant_figures(extract(data, metric_path))
    var i = 0
    return color_categories.map(function(category){
        var filtered_data = data.filter(function (d){return _.get(d, color_key) == category})
        var aggregated_data = aggregate(filtered_data, 'date', metric_path, average, 'metric_avg', null)
        series = {
            name: category,
            data: aggregated_data.map(function(d){return [parseInt(d['date']), d['metric_avg']]}),
            yAxis: 0,
            type: 'line',
            marker: {
                enabled: true,
                radius: 5,
                lineWidth: 1
            },
            tooltip: {
                pointFormatter: function(){return format_point_tooltip(color_key + " " + category, this.x, this.y, 'date', metric_name, '', nb_decimal);}
            },
            color: colour_palette[i],
        }
        if (smooth_line){
            series.regression = true
            series.regressionSettings = { type: 'loess', loessSmooth: 15, color: colour_palette[i], name: "smooth " + category }
            series.type = 'scatter'
        }
        i += 1;
        return series

    })
}

function init_lane_sequencing_metrics_chart(urls, token, merge_on, merge_properties, metric_list, color_list){
    // create the buttons for the metrics
    _.forEach(metric_list, function(m){
        var li = $('#button_' + m.name);
        var button = $('<a>').attr('target', m.name).text(m['title']);
        button.click(function() {
            $('#selected_metric').text(this.text);
            $('#selected_metric').attr('target', this.target);
            render_lane_sequencing_metrics_chart(
                $('#selected_metric').attr('target'),
                $('#selected_color').attr('target'),
                $('#selected_plot_type').attr('target')
            );
        });
        li.append(button);
        // populate the global metrics object.
        lane_metrics[m.name]=m
    })

    // create the buttons for the color
    _.forEach(color_list, function(c){
        var li = $('#button_' + c.name);
        var button = $('<a>').attr('target', c.name).text(c['title']);
        button.click(function() {
            $('#selected_color').text(this.text)
            $('#selected_color').attr('target', this.target)
            render_lane_sequencing_metrics_chart(
                $('#selected_metric').attr('target'),
                $('#selected_color').attr('target'),
                $('#selected_plot_type').attr('target')
            );
        });
        li.append(button);
        // populate the global metrics object.
        color_options[c.name]=c
    })

    // create the buttons for the plot type
     _.forEach(plot_options, function(p){
        var li = $('#button_' + p['name']);
        var button = $('<a>').attr('target', p['name']).text(p['title']);
        button.click(function() {
            $('#selected_plot_type').text(this.text)
            $('#selected_plot_type').attr('target', this.target)
            render_lane_sequencing_metrics_chart(
                $('#selected_metric').attr('target'),
                $('#selected_color').attr('target'),
                $('#selected_plot_type').attr('target')
            );
        });
        li.append(button);
    })


    chart = Highcharts.chart('highchart_cont', {
        chart: {
            zoomType: 'x'
        },
        title: {
            text: 'Sequencing metrics: ' ,
        },
        xAxis: {
            type: 'datetime',
            title: { text: 'Date' }
        },
        yAxis: [ { title: { text: '' } }],
        series: [],
        plotOptions: { series: { softThreshold: true, turboThreshold: 0 }  },
        credits: false
    });
    // Load the data and store it for later use
    chart.showLoading();
    ajax_call_function = merge_multi_sources_keep_first(urls, token, merge_on, merge_properties)
    ajax_call_function(null, function(json){
        lane_data = json['data']
        // Remove lanes from runs where the Run did not complete
        lane_data = lane_data.filter(function(element){
            return _.get(element, 'run.run_status', 'RunCompleted') == 'RunCompleted'
        });
        // Adds date and sequencer to the data structure by parsing the run name
        lane_data.map(function(element) {
            run_id_split = element['run_id'].split('_')
            element['date'] = moment(run_id_split[0], 'YYMMDD').valueOf();
            element['sequencer'] = run_id_split[1];
            element['sequencer_stage'] = run_id_split[1] + '_' + run_id_split[3].substring(0, 1);
            element['pool'] = element['run_elements'].length > 1 ? 'pooling' : 'non_pooling';
        });
        chart.hideLoading();
    });
}

function render_lane_sequencing_metrics_chart(metric_id, color_id, plot_type){
    if (metric_id == "" || color_id == "" || plot_type == ""){ return }
    // Create the new series
    var series = plot_options[plot_type]['function'](
        lane_data,
        color_options[color_id].data,
        lane_metrics[metric_id].data,
        lane_metrics[metric_id].title
    )
    // Remove the previous series
    _.forEachRight(chart.series, function(s) { s.remove(); });
    // Add the new series
    _.forEach(series, function(s){chart.addSeries(s, false)});
    //Title
    var title = plot_options[plot_type].title + ' of ' + lane_metrics[metric_id].title + ' per ' + color_options[color_id].title

    chart.yAxis[0].update({ title: { text: lane_metrics[metric_id].title } })
    chart.title.update({ text: title })
    chart.legend.update({
        title: {
            text: color_options[color_id].title,
            align: 'center',
            fontWeight: 'bold'
        }
    });
}

// Load the ajax call and call the call back method
function load_ajax_call(url, token, callback){
    $.ajax({
        url: url,
        dataType: "json",
        async: true,
        headers: {'Authorization': token},
        success: function(json) {
            if (callback !== undefined){
                callback(json);
            }
        }
    });
}

