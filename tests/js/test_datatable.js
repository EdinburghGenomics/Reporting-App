
QUnit.test('datatable', function(assert) {

    assert.equal(
        merge_on(
            [
                [{'sample_id': 'sample_1', 'this': 1}, {'sample_id': 'sample_2', 'this': 2}, {'sample_id': 'sample_3', 'this': 3}],
                [{'sample_id': 'sample_3', 'that': 2}, {'sample_id': 'sample_1', 'that': 3}, {'sample_id': 'sample_2', 'that': 4}]
            ],
            'sample_id'
        ).toString(),
        [
            {'sample_id': 'sample_1', 'this': 1, 'that': 3},
            {'sample_id': 'sample_2', 'this': 2, 'that': 4},
            {'sample_id': 'sample_3', 'this': 3, 'that': 2}
        ].toString()
    );

});
