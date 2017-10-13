
QUnit.test('string_formatter', function(assert) {
    row = {}
    assert.equal(
        string_formatter(13.37, {'type': 'percentage'}, row),
        '<div class="dt_cell">13.4%</div>'
    );

    assert.equal(
        string_formatter(0.1337, {'type': 'ratio_percentage'}, row),
        '<div class="dt_cell">13.4%</div>'
    );

    assert.equal(
        string_formatter(1337, {'type': 'int'}, row),
        '<div class="dt_cell">1,337</div>'
    );

    assert.equal(
        string_formatter(1.337, {'type': 'float'}, row),
        '<div class="dt_cell">1.34</div>'
    );

    assert.equal(
        string_formatter('Thu, 20 Apr 2017 15:09:56 GMT', {'type': 'date'}, row),
        '<div class="dt_cell">2017-04-20</div>'
    );

    assert.equal(
        string_formatter('2017-04-20T15:09:56.013000Z', {'type': 'date'}, row),
        '<div class="dt_cell">2017-04-20</div>'
    );

    assert.equal(
        string_formatter('Thu, 20 Apr 2017 15:09:56', {'type': 'datetime'}, row),
        '<div class="dt_cell">2017-04-20 15:09:56</div>'
    );

    assert.equal(
        string_formatter('2017-04-20T15:09:56.013000', {'type': 'datetime'}, row),
        '<div class="dt_cell">2017-04-20 15:09:56</div>'
    );

    assert.equal(
        string_formatter(1, {'min': 1, 'max': 3}, row),
        '<div class="dt_cell">1</div>'
    );

    assert.equal(
        string_formatter(3, {'min': 1, 'max': 3}, row),
        '<div class="dt_cell">3</div>'
    );

    assert.equal(
        string_formatter(0, {'min': 1, 'max': 3}, row),
        '<div class="dt_cell"><div style="color:red">0</div></div>'
    );

    assert.equal(
        string_formatter(4, {'min': 1, 'max': 3}, row),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    assert.equal(
        string_formatter(4, {'min': {'field':'nothere', 'default': 5}}, row),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    row = {'real_field': 5}
    assert.equal(
        string_formatter(4, {'min': {'field':'real_field', 'default': 4}}, row),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    assert.equal(
        string_formatter(6, {'min': {'field':'real_field', 'default': 6}}, row),
        '<div class="dt_cell">6</div>'
    );

});
