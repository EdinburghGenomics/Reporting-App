




QUnit.test('dt_merge_multi_sources', function(assert) {
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
    dt_merge_multi_sources(dt_config)('some_data', callback, 'some_settings')

    assert.deepEqual(
        observed_data,
        [
            {sample_id: 'sample_1', x: 1, y: 4},
            {sample_id: 'sample_2', x: 2, y: 3}
        ]
    );

    $.ajax = original_ajax;  // end patch
});


QUnit.test('get_run_review', function(assert) {
    // Mock a datatable config
    var dt_config = {review_entity_field: 'sample_ids'};
    var e, node, config;
    // Mock a datatables object
    var dt = {
        rows: function() {
            return {
                data: function() {
                    return [{'sample_ids': ['sample1', 'sample2']}]
                }
            }
        }
    }

    // Mock html elements that will interact with the function
    var modaltext = document.createElement('div');
    modaltext.setAttribute('id', 'modaltext');
    var reviewModal = document.createElement('div');
    reviewModal.setAttribute('id', 'reviewModal');
    reviewModal.appendChild(modaltext);
    document.body.appendChild(reviewModal);

    lims_run_review(dt_config)(e, dt, node, config);
    assert.equal(
        modaltext.innerHTML,
        'About to review the usability of run elements from 2 samples:<br>sample1<br>sample2'
    )

});

QUnit.test('configure_buttons', function(assert) {
    assert.deepEqual(
        configure_buttons({'buttons': ['colvis']}),
        [{extend: 'colvis', text: '<i class="fa fa-filter"></i>', titleAttr: 'Filter Columns'}]
    );
});


QUnit.test('required_yields', function(assert) {
    var test_data = {};

    // patching ajax
    var original_ajax = $.ajax;
    var fake_ajax = function(config) {
        config.success(
            {
                'data': [{'aggregated': {
                    'required_yield': {'15X': 10, '30X': 20},
                    'required_yield_q30': {'15X': 8, '30X': 16}
                }}]
            }
        );
    };
    $.ajax = fake_ajax;
    // patching complete

    var captured_result;
    var fake_callback = function(cfg) {
        captured_result = cfg;
    };

    var _required_yields = required_yields({'ajax_call': {'api_url': 'a_url'}});
    _required_yields(undefined, fake_callback, undefined);

    assert.deepEqual(
        captured_result.data,
        [
            {'coverage': {'order': '15', 'disp': '15X'}, 'required_yield': 10, 'required_yield_q30': 8},
            {'coverage': {'order': '30', 'disp': '30X'}, 'required_yield': 20, 'required_yield_q30': 16}
        ]
    )

    $.ajax = original_ajax;  // end patch
});

// TODO: test sum_row_per_column
