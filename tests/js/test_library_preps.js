
QUnit.test('query_nested_object', function(assert) {
    var o = {'this': {'that': {'other': 1}}};

    assert.deepEqual(query_nested_object(o, 'this'), {'that': {'other': 1}});
    assert.equal(query_nested_object(o, 'this.that.other'), 1);
    assert.equal(query_nested_object(o, 'this.another.more'), null);
});

QUnit.test('format_library_series', function(assert) {
    var library = {
        'id': 'a_library',
        'preps': {
            'a_prep': {
                'date_run': 'a_date',
                'qc': {
                    'A:1': {
                        'name': 'a_sample',
                        'udf': {'a_udf': 13.37},
                        'sample': {'a_rest_api_metrics': 13.38}
                    }
                }
            }
        }
    };

    assert.deepEqual(
        format_library_series(library, 'a_qc_metric'),
        {
            name: library['id'],
            borderWidth: 1,
            data: [
                {'y': 0, 'x': 0, 'value': 13.37, 'name': 'a_sample'}
            ],
            dataLabels: {
                enabled: false,
                color: '#000000'
            }
        }
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
                {'placements': [{'name': 'sample_1'}, {'name': 'sample_2'}]},
                {'placements': [{'name': 'sample_3'}, {'name': 'sample_4'}]}
            ],
            [
                {'sample_id': 'sample_1', 'some': 'rest', 'api': 'data'},
                {'sample_id': 'sample_2', 'some': 'rest', 'api': 'data'}
            ],
            [
                {'sample_id': 'sample_3', 'some': 'rest', 'api': 'data'},
                {'sample_id': 'sample_4', 'some': 'rest', 'api': 'data'}
            ]
        ];
        mock_url_calls.push(config.url);
        ajax_number++;
        var result = {data: side_effects[ajax_number]};
        config.success(result);
    };
    $.ajax = fake_ajax;
    // patching complete

    assert.deepEqual(
        get_lims_and_qc_data(
            'lims_endpoint',
            'qc_url',
            "Token a_token",
            null,
            null,
            'a_library'
        ),
        [
            {
                'placements': [
                    {'name': 'sample_1', 'qc': {'sample_id': 'sample_1', 'some': 'rest', 'api': 'data'}},
                    {'name': 'sample_2', 'qc': {'sample_id': 'sample_2', 'some': 'rest', 'api': 'data'}}
                ]
            },
            {
                'placements': [
                    {'name': 'sample_3', 'qc': {'sample_id': 'sample_3', 'some': 'rest', 'api': 'data'}},
                    {'name': 'sample_4', 'qc': {'sample_id': 'sample_4', 'some': 'rest', 'api': 'data'}}
                ]
            }
        ]
    );
    assert.deepEqual(
        mock_url_calls,
        [
            'lims_endpoint?library_id=a_library',
            'qc_url?where={"$or":[{"sample_id":"sample_1"},{"sample_id":"sample_2"}]}&max_results=1000',
            'qc_url?where={"$or":[{"sample_id":"sample_3"},{"sample_id":"sample_4"}]}&max_results=1000'
        ]
    );
    $.ajax = original_ajax;
});
