
QUnit.test('aggregate_on_date', function(assert) {
    var data = [
        {'date': new Date('14 December 2017'), 'a_field': 1, 'another_field': 2},
        {'date': new Date('14 December 2017'), 'a_field': 3, 'another_field': 4},
        {'date': new Date('6 December 2017'), 'a_field': 5, 'another_field': 6}
    ]



    var fields = [
        {'name': 'a_field'},
        {'name': 'another_field'}
    ]

    assert.deepEqual(
        aggregate_on_date(data, 'month', fields),
        {'Sat Dec 16 2017 11:59:59 GMT+0000': {'a_field': 9, 'another_field': 12}}
    );
    assert.deepEqual(
        aggregate_on_date(data, 'week', fields),
        {
            'Wed Dec 06 2017 11:59:59 GMT+0000': {
                'a_field': 5,
                'another_field': 6
            },
            'Wed Dec 13 2017 11:59:59 GMT+0000': {
                'a_field': 4,
                'another_field': 6
            }
        }
    );
});


QUnit.test('unwind_samples_sequenced', function(assert) {
    var run_elements = [
        {'sample_id': 'a_sample', 'run_id': '171212_run'},
        {'sample_id': 'a_sample', 'run_id': '171211_run'},
        {'sample_id': 'another_sample', 'run_id': '171212_run'},
    ]

    assert.deepEqual(
        unwind_samples_sequenced(run_elements),
        [
            {
                'date': new Date('11 Dec 2017'),
                'first': 1,
                'repeat': 0,
                'total': 1
            },
            {
                'date': new Date('12 Dec 2017'),
                'first': 0,
                'repeat': 1,
                'total': 1
            },
            {
                'date': new Date('12 Dec 2017'),
                'first': 1,
                'repeat': 0,
                'total': 1
            }
        ]
    );
});


QUnit.test('sort_dict_by_date', function(assert) {
    var data = {
        'Wed Dec 06 2017 12:00:00 GMT+0000': 'some_data',
        'Wed Dec 30 2017 12:00:00 GMT+0000': 'some_data',
        'Wed Dec 13 2017 12:00:00 GMT+0000': 'some_data',
        'Wed Dec 03 2017 12:00:00 GMT+0000': 'some_data'
    }

    assert.deepEqual(
        sortDictByDate(data),
        data = {
            'Wed Dec 03 2017 12:00:00 GMT+0000': 'some_data',
            'Wed Dec 06 2017 12:00:00 GMT+0000': 'some_data',
            'Wed Dec 13 2017 12:00:00 GMT+0000': 'some_data',
            'Wed Dec 30 2017 12:00:00 GMT+0000': 'some_data',
        }
    );
});


QUnit.test('add_cumulative', function(assert) {
    var fields = [{'name': 'yield_in_gb'}, {'name': 'yield_q30_in_gb'}];
    var data = {
        'Wed Dec 03 2017': {
            'yield_in_gb': 7677,
            'yield_q30_in_gb': 6348
        },
        'Wed Dec 06 2017': {
            'yield_in_gb': 1338,
            'yield_q30_in_gb': 1337
        }
    }

    add_cummulative(data, fields)

    assert.deepEqual(
        data,
        {
            'Wed Dec 03 2017': {
                'cumm_yield_in_gb': 7677,
                'cumm_yield_q30_in_gb': 6348,
                'yield_in_gb': 7677,
                'yield_q30_in_gb': 6348
            },
            'Wed Dec 06 2017': {
                'cumm_yield_in_gb': 9015,
                'cumm_yield_q30_in_gb': 7685,
                'yield_in_gb': 1338,
                'yield_q30_in_gb': 1337
            }
        }
    );
});


QUnit.test('format_week', function(assert) {
    var date = 'Wed Dec 03 2017 12:00:00 GMT+0000';
    assert.deepEqual(
        format_week(date),
        {
            'v': new Date(date),
            'f': 'week 49 2017 (03/12 -  09/12)'
        }
    );
});


QUnit.test('format_month', function(assert) {
    var date = 'Wed Dec 03 2017 12:00:00 GMT+0000';
    assert.deepEqual(
        format_month(date),
        {
            'v': new Date(date),
            'f': 'Dec 2017'
        }
    );
});


QUnit.test('add_percentage', function(assert) {
    var data = {
        'this': {
            'that': 4,
            'other': 10
        },
        'another': {
            'that': 9,
            'other': 12
        }
    }

    add_percentage(data, 'that', 'other', 'proportion')
    assert.deepEqual(
        data,
        {
            'another': {
                'other': 12,
                'proportion': 0.75,
                'that': 9
            },
            'this': {
                'other': 10,
                'proportion': 0.4,
                'that': 4
            }
        }
    );
});


QUnit.test('merge_objects', function(assert) {
    var obj1 = {
        'x': {
            'this': 0, 'that': 1
        },
        'y': {
            'this': 2
        }
    };

    var obj2 = {
        'x': {
            'other': 3, 'that': 4
        },
        'y': {
            'other': 5
        }
    };

    assert.deepEqual(
        merge_dict_of_object(obj1, obj2),
        {
            'x': {
                'this': 0, 'that': 4, 'other': 3
            },
            'y': {
                'this': 2, 'other': 5
            }
        }
    );
});


