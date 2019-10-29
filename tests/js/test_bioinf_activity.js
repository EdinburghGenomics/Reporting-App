
QUnit.test('entity_running_days', function(assert) {
    var entities_by_date = {
        1546300800000: 0,  // 2019-01-01
        1546387200000: 0,  // 2019-01-02
        1546473600000: 0,  // 2019-01-03
        1546560000000: 0,  // 2019-01-04
    }

    add_entity_running_days(
        {'start': '01_01_2019_12:00:00', 'end': '02_01_2019_10:00:00'},
        entities_by_date, 'start', 'end'
    );
    add_entity_running_days(
        {'start': '02_01_2019_17:00:00', 'end': '03_01_2019_09:00:00'},
        entities_by_date, 'start', 'end'
    );
    assert.deepEqual(
        entities_by_date,
        {
            1546300800000: 1,
            1546387200000: 2,
            1546473600000: 1,
            1546560000000: 0
        }
    );
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
            moment.utc('2019-01-01'),
            moment.utc('2019-01-05')
        ),
        {
            'name': 'a_series',
            'data': [
                [moment.utc('2019-01-01').valueOf(), 3],
                [moment.utc('2019-01-02').valueOf(), 2],
                [moment.utc('2019-01-03').valueOf(), 0],
                [moment.utc('2019-01-04').valueOf(), 1],
                [moment.utc('2019-01-05').valueOf(), 1]
            ]
        }
    );
});
