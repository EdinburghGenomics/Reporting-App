
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

QUnit.test('get_run_review', function(assert) {
    // Mock a datatable config
    var dt_config = {run_review_field: 'sample_ids'};
    var e, node, config;
    // Mock a datatables object
    var dt = {rows: function() { return { data: function() { return [
        { 'sample_ids': ['sample1', 'sample2']}
    ]}}}}

    // Mock html elements that will interact with the function
    var modaltext = document.createElement("div");
    modaltext.setAttribute("id", "modaltext");
    var reviewModal = document.createElement("div");
    reviewModal.setAttribute("id", "reviewModal");
    reviewModal.appendChild(modaltext);
    document.body.appendChild(reviewModal);

    f = get_run_review(dt_config)(e, dt, node, config);
    assert.equal(modaltext.textContent, "You're about to review the usability of run elements from 2 samples:sample1sample2")

});

QUnit.test('configure_buttons', function(assert) {
    assert.deepEqual(
        configure_buttons({'buttons':['colvis']}),
        [{extend: 'colvis', text: '<i class="fa fa-filter"></i>', titleAttr: 'Filter Columns'}]
    );
});

// TODO: test sum_row_per_column
