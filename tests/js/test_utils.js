
QUnit.test('merge_on_key', function(assert) {
    var datasrc1 = [{sample_id: 'sample_1', x: 1}, {sample_id: 'sample_2', x: 2}];
    var datasrc2 = [{sample_id: 'sample_2', y: 3}, {sample_id: 'sample_1', y: 4}];  // order within the data should not matter...
    var datasrc3 = [{sample_id: 'sample_1', x: 5}];  // should override x in datasrc1 as it's merged last

    assert.deepEqual(
        merge_on_key(
            [datasrc1, datasrc2, datasrc3],
            'sample_id'
        ),
        [
            {sample_id: 'sample_1', x: 5, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );
});


QUnit.test('merge_on_key_keep_first_sub_properties', function(assert) {
    var datasrc1 = [{lane: '1', x: 1, run_id: 'run1'}, {lane: '2', x: 2, run_id: 'run1'}, {lane: '1', x: 3, run_id: 'run2'}];
    var datasrc2 = [{run_id: 'run1', y: 1}, {run_id: 'run2', y: 4}, {run_id: 'run3', y: 10}];  // run_3 should be ignored

    // Test with no key for the subsequent queries
    assert.deepEqual(
        merge_on_key_keep_first_sub_properties(
            [datasrc1, datasrc2],
            'run_id'
        ),
        [
            {lane: '1', x: 1, run_id: 'run1', y: 1},
            {lane: '2', x: 2, run_id: 'run1', y: 1},
            {lane: '1', x: 3, run_id: 'run2', y: 4}
        ]
    );

    // Test with one key for the subsequent query
    assert.deepEqual(
        merge_on_key_keep_first_sub_properties(
            [datasrc1, datasrc2],
            'run_id',
            ['d2']
        ),
        [
            {lane: '1', x: 1, run_id: 'run1', 'd2': {y: 1, run_id: 'run1'}},
            {lane: '2', x: 2, run_id: 'run1', 'd2': {y: 1, run_id: 'run1'}},
            {lane: '1', x: 3, run_id: 'run2', 'd2': {y: 4, run_id: 'run2'}}
        ]
    );

    var datasrc1 = [{lane: '1', x: 1, run_id: 'run1'}, {lane: '2', x: 2, run_id: 'run1'}, {lane: '1', x: 3, run_id: 'run2'}];
    var datasrc2 = [{run_id: 'run1', y: 1}, {run_id: 'run2', y: 4}, {run_id: 'run3', y: 10}];  // run_3 should be ignored
    var datasrc3 = [{run_id: 'run1', z: 'a'}, {run_id: 'run2', z: 'b'}, {run_id: 'run3', z: 'c'}];  // run_3 should be ignored

    // Test with list of keys for the subsequent queries
    assert.deepEqual(
        merge_on_key_keep_first_sub_properties(
            [datasrc1, datasrc2, datasrc3],
            'run_id',
            ['d2', 'd3']
        ),
        [
            {lane: '1', x: 1, run_id: 'run1', 'd2': {y: 1, run_id: 'run1'}, 'd3': {z: 'a', run_id: 'run1'}},
            {lane: '2', x: 2, run_id: 'run1', 'd2': {y: 1, run_id: 'run1'}, 'd3': {z: 'a', run_id: 'run1'}},
            {lane: '1', x: 3, run_id: 'run2', 'd2': {y: 4, run_id: 'run2'}, 'd3': {z: 'b', run_id: 'run2'}}
        ]
    );

    // Test with list of keys including on null
    assert.deepEqual(
        merge_on_key_keep_first_sub_properties(
            [datasrc1, datasrc2, datasrc3],
            'run_id',
            [null, 'd3']
        ),
        [
            {lane: '1', x: 1, run_id: 'run1', y: 1, 'd3': {z: 'a', run_id: 'run1'}},
            {lane: '2', x: 2, run_id: 'run1', y: 1, 'd3': {z: 'a', run_id: 'run1'}},
            {lane: '1', x: 3, run_id: 'run2', y: 4, 'd3': {z: 'b', run_id: 'run2'}}
        ]
    );
});


QUnit.test('merge_multi_sources', function(assert) {
    // patching ajax
    var original_ajax = $.ajax;
    var fake_ajax = function(config) {
        var data;
        if (config.url == 'an_api_url') {
            data = [
                {sample_id: 'sample_1', x: 1},
                {sample_id: 'sample_2', x: 2}
            ]
        } else if (config.url == 'another_api_url') {
            data = [
                {sample_id: 'sample_2', y: 3},
                {sample_id: 'sample_1', y: 4}
            ]
        }
        return [{data: data}];
    };
    $.ajax = fake_ajax;
    // patching complete

    var observed_data;
    var callback = function(x) {
        observed_data = x.data;  // capture the results of merge_multi_sources
    }

    merge_multi_sources(['an_api_url', 'another_api_url'], 'sample_id')('some_data', callback, 'some_settings')

    assert.deepEqual(
        observed_data,
        [
            {sample_id: 'sample_1', x: 1, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );

    $.ajax = original_ajax;  // end patch
});

QUnit.test('merge_lims_container_and_qc_data', function(assert) {
    // patching ajax
    var original_ajax = $.ajax;
    var ajax_number = -1;
    var mock_url_calls = [];
    var fake_ajax = function(config) {
        var side_effects = [
            [
                {'name': 'sample_1', 'location': 'A:1', 'udfs': {'some': 'lims', 'udf': 'data'}},
                {'name': 'sample_2', 'location': 'A:2', 'udfs': {'some': 'more', 'lims': 'data'}}
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

    // Get the function that datatable will call
    func = merge_lims_container_and_qc_data('lims_endpoint', 'qc_url', 'a_library');
    // Create the call back where the test will occur
    var test_callback = function(data_json){
        assert.deepEqual(
        data_json,
        {
            'data': [
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
            ],
            'recordsFiltered': 2,
            'recordsTotal': 2
        }
    );
    }
    // Call the cuntion as datatables would: this will run the test
    func(null, test_callback, null)

    assert.deepEqual(
        mock_url_calls,
        [
            'lims_endpoint',
            'qc_url?where={"$or":[{"sample_id":"sample_1"},{"sample_id":"sample_2"}]}&max_results=1000'
        ]
    );
    $.ajax = original_ajax;
});


QUnit.test('test_exist', function(assert) {
    var t;
    assert.notOk(test_exist(t));
    assert.notOk(test_exist(null));
    assert.notOk(test_exist(''));
    assert.notOk(test_exist([]));
    assert.notOk(test_exist([null]));
    assert.ok(test_exist('1, 2, 3'));
    assert.ok(test_exist(['1', '2', '3']));
});

//Commented out because it does not pass in phantomJS
//QUnit.test('test_significant_figures', function(assert) {
//    var list_number = [1, 2, 4, 7, 2, 5];
//    assert.equal(significant_figures(list_number), 0)
//
//    list_number = [1.868, 0.293, 2.1274, 1.4728, 1.3457, 0.71895];
//    assert.equal(significant_figures(list_number), 2)
//
//    list_number = [10.868, 67.293, 54.1274, 23.4728, 7.3457, 61.71895];
//    assert.equal(significant_figures(list_number), 1)
//
//    list_number = [1245.868, 7347.293, 2684.1274, 930.4728, 2535.3457, 1651.71895];
//    assert.equal(significant_figures(list_number), 0)
//
//});


QUnit.test('getPercentile', function(assert) {
    assert.equal(
        getPercentile([10, 4, 23, 41, 32, 58, 29], 50),
        29
    );
})

var list_object = [
    {'x': 1, 'y': 2},
    {'x': 2, 'y': 2},
    {'x': 3, 'y': 2},
    {'x': 2, 'y': 4},
    {'x': 42, 'y': 4}
]

QUnit.test('sum', function(assert) {
    assert.equal(sum(list_object, 'x'), 50);
})

QUnit.test('average', function(assert) {
    assert.equal(average(list_object, 'x'), 10);
})

QUnit.test('count', function(assert) {
    assert.equal(count(list_object, 'x'), 5);
})

QUnit.test('extract', function(assert) {
    assert.deepEqual(extract(list_object, 'x'), [1, 2, 3, 2, 42]);
})

QUnit.test('boxplot_values_outliers', function(assert) {
    box = boxplot_values_outliers(list_object, 'x')
    assert.deepEqual(box.values, [1, 2, 2, 3, 3]);
    assert.deepEqual(box.outliers, [42]);
})

QUnit.test('format_time_period', function(assert) {
    d = moment('2018-06-22T00:00:00Z').valueOf()
    assert.equal(format_time_period('date', d), '22 Jun 2018');
    assert.equal(format_time_period('week', d), 'Week 25 2018');
    assert.equal(format_time_period('month', d), 'Jun 2018');
    assert.equal(format_time_period('quarter', d), 'Q2 2018');
})

QUnit.test('format_y_point', function(assert) {
    assert.deepEqual(format_y_point(1.234, 'prefix', 'suffix', 1), 'prefix 1.2 suffix');
    assert.deepEqual(format_y_point(1, 'prefix', 'suffix', 1    ), 'prefix 1.0 suffix');
})

QUnit.test('format_y_boxplot', function(assert) {
    options = {low: 2.0, q1: 3.0, median: 4.0, q3: 5.0, high: 6.0}
    expected_html = 'low: prefix 2 suffix<br>25pc: prefix 3 suffix<br>Median: prefix 4 suffix<br>75pc: prefix 5 suffix<br>high: prefix 6 suffix'
    assert.equal(format_y_boxplot(options, 'prefix', 'suffix'), expected_html);
})

QUnit.test('aggregate', function(assert) {
    assert.deepEqual(
        aggregate(list_object, 'y', ['x', 'x'], [average, count], ['average_x', 'count_x'], null),
        [{y: "2", average_x: 2, count_x: 3}, {y: "4", average_x: 22, count_x:2}]
    );

    var list_object2 = [
        {'x': 1, 'y': 2},
        {'x': 2, 'y': 2},
        {'x': 3, 'y': 2},
        {'x': 2, 'y': 4},
        {'x': 0, 'y': 4}
    ];
    assert.deepEqual(
        aggregate(list_object2, 'y', ['x', 'x'], [average, count], ['average_x', 'count_x'], null),
        [{y: "2", average_x: 2, count_x: 3}, {y: "4", average_x: 1, count_x:2}]
    );

    list_object2 = [
        {'x': 1, 'y': 2},
        {'x': 2, 'y': 2},
        {'x': 3, 'y': 2},
        {'x': 2, 'y': 4},
        {'x': null, 'y': 4}
    ]
    // Null values should be filtered out
    assert.deepEqual(
        aggregate(list_object2, 'y', ['x', 'x'], [average, count], ['average_x', 'count_x'], null),
        [{y: "2", average_x: 2, count_x: 3}, {y: "4", average_x: 2, count_x:1}]
    );
})

QUnit.test('depagination', function(assert) {
    // patching jquery
    var original_ajax = $.ajax;
    var original_when = $.when;

    var fake_then = function(func) { func(fake_deferreds[0], fake_deferreds[1]);};
    var fake_when = {
        apply: function(jq, calls) {
            return {then: fake_then}
        }
    };

    var fake_ajax_calls = 0;
    var fake_deferreds = [];

    var fake_ajax_responses = [
        {data: ['sample_1', 'sample_2'], _meta: {total: 5, max_results: 2}},
        {data: ['sample_3', 'sample_4']},
        {data: ['sample_5']}
    ];

    var fake_ajax = function(config) {
        var data = fake_ajax_responses[fake_ajax_calls];
        fake_ajax_calls += 1;

        if (config.success) {
            config.success(data);
        } else {
            fake_deferreds.push([data]);
        }
    };
    $.ajax = fake_ajax;
    $.when = fake_when;
    // patching complete

    // full depagination of >2 pages
    var obs = null;
    depaginate('http://base_url', {}, function(data) { obs = data;});
    assert.deepEqual(obs, ['sample_1', 'sample_2', 'sample_3', 'sample_4', 'sample_5']);
    assert.equal(fake_ajax_calls, 3);

    // depagination of 2 pages
    obs = null;
    fake_ajax_calls = 0;
    fake_ajax_responses = [
        {data: ['sample_1', 'sample_2'], _meta: {total: 3, max_results: 2}},
        {data: ['sample_3']}
    ];
    depaginate('http://base_url', {}, function(data) { obs = data;});
    assert.deepEqual(obs, ['sample_1', 'sample_2', 'sample_3']);
    assert.equal(fake_ajax_calls, 2);


    // depagination of 1 page
    obs = null;
    fake_ajax_calls = 0;
    fake_ajax_responses = [{data: ['sample_1', 'sample_2'], _meta: {total: 2, max_results:2}}];

    depaginate('http://base_url', {}, function(data) { obs = data;});
    assert.deepEqual(obs, ['sample_1', 'sample_2']);
    assert.equal(fake_ajax_calls, 1);

    // end patch
    $.ajax = original_ajax;
    $.when = original_when;
    fake_ajax_calls = 0;
});
