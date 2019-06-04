
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

QUnit.test('format_y_suffix', function(assert) {
    assert.deepEqual(format_y_suffix(1, 'prefix', 'suffix'), 'prefix 1.0 suffix');
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
})
