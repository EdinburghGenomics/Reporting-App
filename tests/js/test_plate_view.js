
QUnit.test('build_series', function(assert) {
    fake_renderer = function(metric) { return metric; };

    container_data = [{
        'id': 'a_library',
        'location': 'A:1',
        'name': 'a_sample',
        'udf': {'a_udf': 13.37},
        'reporting_app': {'a_rest_api_metric': 13.38}
    }];
    heatmap_y_category = 'ABCDEFGH';
    metrics = {
        'a_metric': {'data': ['reporting_app', 'a_rest_api_metric']},
        'another_metric': {'data': ['udf', 'a_udf']}
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

