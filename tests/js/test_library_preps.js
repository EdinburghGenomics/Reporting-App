
QUnit.test('query_nested_object', function(assert) {
    var o = {'this': {'that': {'other': 1}}};

    assert.deepEqual(query_nested_object(o, ['this']), {'that': {'other': 1}});
    assert.equal(query_nested_object(o, ['this', 'that', 'other']), 1);
    assert.equal(query_nested_object(o, ['this', 'another', 'more']), null);
});

QUnit.test('build_series', function(assert) {
    fake_renderer = function(metric) { return metric; };

    library_data = {
        'id': 'a_library',
        'qc': {
            'A:1': {
                'name': 'a_sample',
                'udf': {'a_udf': 13.37},
                'reporting_app': {'a_rest_api_metric': 13.38}
            }
        }
    };
    metrics = {
        'a_metric': {'path': ['reporting_app', 'a_rest_api_metric']},
        'another_metric': {'path': ['udf', 'a_udf']}
    };

    assert.deepEqual(
        build_series('a_metric', fake_renderer),
        {
            name: 'a_library',
            data: [
                {'y': 0, 'x': 0, 'value': 13.38, 'name': 'a_sample'}
            ],
            dataLabels: {enabled: false}
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
                    'qc': {
                        'A:1': {'name': 'sample_1', 'udf': {'some': 'lims', 'udf': 'data'}},
                        'A:2': {'name': 'sample_2', 'udf': {'some': 'more', 'lims': 'data'}}
                    }
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
    // patching complete

    chart = {
        addSeries: function(config) {},
        hideLoading: function() {},
        series: [{update: function(config) {}}],
        legend: {update: function(config) {}},
        colorAxis: [{update: function(config) {}}]
    };
    metrics = {'a_metric': {'path': ['reporting_app', 'api']}};
    active_colour_metric = 'a_metric';

    get_lims_and_qc_data('lims_endpoint', 'qc_url', 'Token a_token', 'a_library');

    assert.deepEqual(
        library_data,
        {
            'qc': {
                'A:1': {
                    'name': 'sample_1',
                    'reporting_app': {
                        'sample_id': 'sample_1',
                        'some': 'rest',
                        'api': 'data'
                    },
                    'udf': {
                        'some': 'lims',
                        'udf': 'data'
                    }
                },
                'A:2': {
                    'name': 'sample_2',
                    'reporting_app': {
                        'sample_id': 'sample_2',
                        'some': 'more',
                        'api': 'data'
                    },
                    'udf': {
                        'some': 'more',
                        'lims': 'data'
                    }
                }
            }
        }
    );
    assert.deepEqual(
        mock_url_calls,
        [
            'lims_endpoint?match={"library_id":"a_library"}',
            'qc_url?where={"$or":[{"sample_id":"sample_1"},{"sample_id":"sample_2"}]}&max_results=1000'
        ]
    );
    $.ajax = original_ajax;
});
