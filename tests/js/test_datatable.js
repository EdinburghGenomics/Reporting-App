
QUnit.test('datatable', function(assert) {

    assert.equal(
        merge_on(
            [
                [{sample_id: 'sample_1', thing: 1}, {sample_id: 'sample_2', thing: 2}, {sample_id: 'sample_3', thing: 3}],
                [{sample_id: 'sample_3', thang: 2}, {sample_id: 'sample_1', thang: 3}, {sample_id: 'sample_2', thang: 4}]
            ],
            'sample_id'
        ).toString(),
        [
            {sample_id: 'sample_1', thing: 1, thang: 3},
            {sample_id: 'sample_2', thing: 2, thang: 4},
            {sample_id: 'sample_3', thing: 3, thang: 2}
        ].toString()
    );

    var ajax = $.ajax;

    $.ajax = function(config) {
        var data;
        if (config.url == 'an_api_url') {
            data = [
                {sample_id: 'a_sample', some_data: 'this'},
                {sample_id: 'another_sample', some_data: 'that'}
            ]
        } else if (config.url == 'another_api_url') {
            data = [
                {sample_id: 'another_sample', some_other_data: 'other'},
                {sample_id: 'a_sample', some_other_data: 'another'}
            ]
        }
        return [{data: data}];
    };

    var dt_config = {ajax_call: {api_urls: ['an_api_url', 'another_api_url'], merge_on: 'sample_id'}}
    var observed_data;
    var callback = function(config) {
        observed_data = config.data;
    }
    merge_multi_sources(dt_config)('some_data', callback, 'some_settings')
    assert.equal(
        observed_data.toString(),
        [
            {sample_id: 'a_sample', some_data: 'this', some_other_data: 'another'},
            {sample_id: 'another_sample', some_data: 'that', some_other_data: 'other'}
        ].toString()
    );
    $.ajax = ajax;

    assert.equal(
        configure_buttons(['colvis']).toString(),
        [{extend: 'colvis', text: '<i class="fa fa-filter"></i>', titleAttr: 'Filter Columns'}].toString()
    );

    // TODO: test sum_row_per_column

});
