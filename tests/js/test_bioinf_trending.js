
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

    var obs = null;
    depaginate('http://base_url', {}, function(data) { obs = data;});
    assert.deepEqual(obs, ['sample_1', 'sample_2', 'sample_3', 'sample_4', 'sample_5']);

    obs = null;
    fake_ajax_calls = 0;
    fake_deferreds = [];
    fake_then = function(func) { func();};
    fake_ajax_responses = [{data: ['sample_1', 'sample_2'], _meta: {total: 2, max_results:2}}];

    depaginate('http://base_url', {}, function(data) { obs = data;});
    assert.deepEqual(obs, ['sample_1', 'sample_2']);

    // end patch
    $.ajax = original_ajax;
    $.when = original_when;
    fake_ajax_calls = 0;
});


QUnit.test('entity_running_days', function(assert) {
    var fmt = 'YYYY-MM-DDTHH:mm:ss';
    var m = moment('2019-01-01T12:00:00', fmt);
    assert.ok(quantise_moment(m).isSame(moment('2019-01-01T00:00:00', fmt)));

    var targets = {};
    add_entity_at('a_date', targets);
    add_entity_at('another_date', targets);
    add_entity_at('a_date', targets);

    assert.deepEqual(targets, {'a_date': 2, 'another_date': 1});

});


QUnit.test('build_series', function(assert) {
    assert.deepEqual(
        build_bioinf_series(
            'a_series',
            [
                {'start': '01_01_2019_00:00:00', 'end': '02_01_2019_00:00:00'},
                {'start': '01_01_2019_23:59:59', 'end': '02_01_2019_00:00:01'},
                {'start': '01_01_2019_12:00:00', 'end': '01_01_2019_12:00:01'},
                {'start': '04_01_2019_12:00:00', 'end': '05_01_2019_12:00:00'}
            ],
            'start',
            'end',
            moment('2019-01-01'),
            moment('2019-01-05')
        ),
        {
            'name': 'a_series',
            'data': [
                [moment('2019-01-01').valueOf(), 3],
                [moment('2019-01-02').valueOf(), 2],
                [moment('2019-01-03').valueOf(), 0],
                [moment('2019-01-04').valueOf(), 1],
                [moment('2019-01-05').valueOf(), 1]
            ]
        }
    );
});