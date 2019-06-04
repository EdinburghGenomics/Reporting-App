
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


QUnit.test('merge_on_key_keep_first_sub_porperties', function(assert) {
    var datasrc1 = [{lane: '1', x: 1, run_id: 'run1'}, {lane: '2', x: 2, run_id: 'run1'}, {lane: '1', x: 3, run_id: 'run2'}];
    var datasrc2 = [{run_id: 'run1', y: 1}, {run_id: 'run2', y: 4}, {run_id: 'run3', y: 10}];  // run_3 should be ignored

    // Test with no key for the subsequent queries
    assert.deepEqual(
        merge_on_key_keep_first_sub_porperties(
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
        merge_on_key_keep_first_sub_porperties(
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
        merge_on_key_keep_first_sub_porperties(
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
        merge_on_key_keep_first_sub_porperties(
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

    merge_multi_sources(['an_api_url', 'another_api_url'], 'token', 'sample_id')('some_data', callback, 'some_settings')

    assert.deepEqual(
        observed_data,
        [
            {sample_id: 'sample_1', x: 1, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );

    $.ajax = original_ajax;  // end patch
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
