
QUnit.test('string_formatter', function(assert) {
    assert.equal(
        string_formatter(13.37, {'type': 'percentage'}),
        '<div class="dt_cell">13.4%</div>'
    );

    assert.equal(
        string_formatter(0.1337, {'type': 'ratio_percentage'}),
        '<div class="dt_cell">13.4%</div>'
    );

    assert.equal(
        string_formatter(1337, {'type': 'int'}),
        '<div class="dt_cell">1,337</div>'
    );

    assert.equal(
        string_formatter(1.337, {'type': 'float'}),
        '<div class="dt_cell">1.34</div>'
    );

    assert.equal(
        string_formatter('Thu, 20 Apr 2017 15:09:56 GMT', {'type': 'date'}),
        '<div class="dt_cell">2017-04-20</div>'
    );

    assert.equal(
        string_formatter(1, {'min': 1, 'max': 3}),
        '<div class="dt_cell">1</div>'
    );

    assert.equal(
        string_formatter(3, {'min': 1, 'max': 3}),
        '<div class="dt_cell">3</div>'
    );

    assert.equal(
        string_formatter(0, {'min': 1, 'max': 3}),
        '<div class="dt_cell"><div style="color:red">0</div></div>'
    );

    assert.equal(
        string_formatter(4, {'min': 1, 'max': 3}),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

});
