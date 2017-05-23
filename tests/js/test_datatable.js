
QUnit.test('merge_on', function(assert) {
    var datasrc1 = [{sample_id: 'sample_1', x: 1}, {sample_id: 'sample_2', x: 2}];
    var datasrc2 = [{sample_id: 'sample_2', y: 3}, {sample_id: 'sample_1', y: 4}];  // order within the data should not matter...
    var datasrc3 = [{sample_id: 'sample_1', x: 5}];  // should override x in datasrc1 as it's merged last

    assert.deepEqual(
        merge_on(
            [datasrc1, datasrc2, datasrc3],
            'sample_id'
        ),
        [
            {sample_id: 'sample_1', x: 5, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );
});

QUnit.test('merge_on_keep_first', function(assert) {
    var datasrc1 = [{sample_id: 'sample_1', x: 1}, {sample_id: 'sample_2', x: 2}];
    var datasrc2 = [{sample_id: 'sample_3', y: 1}, {sample_id: 'sample_1', y: 4}];  // sample_3 should be ignored
    var datasrc3 = [{sample_id: 'sample_1', x: 5}, {sample_id: 'sample_2', y: 3}];

    assert.deepEqual(
        merge_on_keep_first(
            [datasrc1, datasrc2, datasrc3],
            'sample_id'
        ),
        [
            {sample_id: 'sample_1', x: 5, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
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

    var dt_config = {ajax_call: {api_urls: ['an_api_url', 'another_api_url'], merge_on: 'sample_id'}}
    merge_multi_sources(dt_config)('some_data', callback, 'some_settings')

    assert.deepEqual(
        observed_data,
        [
            {sample_id: 'sample_1', x: 1, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );

    $.ajax = original_ajax;  // end patch
});


QUnit.test('configure_buttons', function(assert) {
    assert.deepEqual(
        configure_buttons(['colvis']),
        [{extend: 'colvis', text: '<i class="fa fa-filter"></i>', titleAttr: 'Filter Columns'}]
    );
});

// TODO: test sum_row_per_column