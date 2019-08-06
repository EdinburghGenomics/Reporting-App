
QUnit.test('build_series', function(assert) {
    fake_renderer = function(metric) { return metric; };

    container_data = {
        'id': 'a_library',
        'samples': [
            {
                'location': 'A:1',
                'name': 'a_sample',
                'udf': {'a_udf': 13.37},
                'reporting_app': {'a_rest_api_metric': 13.38}
            }
        ]
    };
    heatmap_y_category = 'ABCDEFGH';
    metrics = {
        'a_metric': {'path': ['reporting_app', 'a_rest_api_metric']},
        'another_metric': {'path': ['udf', 'a_udf']}
    };

    assert.deepEqual(
        build_series('a_metric', fake_renderer),
        {
            name: 'a_library',
            dataLabels: {enabled: false},
            data: [
                {'y': 0, 'x': 0, 'value': 13.38, 'name': 'a_sample'}
            ]
        }
    );
    assert.equal(
        build_series('another_metric', fake_renderer)['data'][0]['value'],
        13.37
    );
});

QUnit.test('get_lims_and_qc_data', function(assert) {
    // patching ajax
    var original_ajax = $.ajax;
    var ajax_number = -1;
    var mock_url_calls = [];
    var fake_ajax = function(config) {
        var side_effects = [
            [
                {
                    'samples': [
                        {'name': 'sample_1', 'location': 'A:1', 'udfs': {'some': 'lims', 'udf': 'data'}},
                        {'name': 'sample_2', 'location': 'A:2', 'udfs': {'some': 'more', 'lims': 'data'}}
                    ]
                }
            ],
            [
                {'sample_id': 'sample_1', 'some': 'rest', 'api': 'data'},
                {'sample_id': 'sample_2', 'some': 'more', 'api': 'data'}
            ]
        ];
        mock_url_calls.push(config.url);
        ajax_number++;
        var result = {data: side_effects[ajax_number]};
        config.success(result);
    };
    $.ajax = fake_ajax;

    // patching chart object
    var fake_func = function(config) {};
    chart = {
        addSeries: fake_func,
        hideLoading: fake_func,
        series: [{update: fake_func, remove: fake_func}],
        legend: {update: fake_func},
        colorAxis: [{update: fake_func}]
    };
    metrics = {'a_metric': {'path': ['reporting_app', 'api']}};
    active_colour_metric = 'a_metric';
    // patching complete

    get_lims_and_qc_data('lims_endpoint', 'qc_url', 'Token a_token', 'a_library');

    assert.deepEqual(
        container_data,
        {
            'samples': [
                {
                    'name': 'sample_1',
                    'location': 'A:1',
                    'bioinformatics_qc': {
                        'sample_id': 'sample_1',
                        'some': 'rest',
                        'api': 'data'
                    },
                    'udfs': {
                        'some': 'lims',
                        'udf': 'data'
                    }
                },
                {
                    'name': 'sample_2',
                    'location': 'A:2',
                    'bioinformatics_qc': {
                        'sample_id': 'sample_2',
                        'some': 'more',
                        'api': 'data'
                    },
                    'udfs': {
                        'some': 'more',
                        'lims': 'data'
                    }
                }
            ]
        }
    );
    assert.deepEqual(
        mock_url_calls,
        [
            'lims_endpoint?match={"container_id":"a_library"}',
            'qc_url?where={"$or":[{"sample_id":"sample_1"},{"sample_id":"sample_2"}]}&max_results=1000'
        ]
    );
    $.ajax = original_ajax;
});
