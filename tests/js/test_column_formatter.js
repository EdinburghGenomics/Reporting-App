
var row = {};


QUnit.test('number formatting', function(assert) {
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
});


QUnit.test('date formatting', function(assert) {
    assert.equal(
        string_formatter('Thu, 20 Apr 2017 15:09:56 GMT', {'type': 'date'}, row),
        '<div class="dt_cell">2017-04-20</div>'
    );

    assert.equal(
        string_formatter('2017-04-20T15:09:56.013000Z', {'type': 'date'}, row),
        '<div class="dt_cell">2017-04-20</div>'
    );

    // I hate MomentJS.
    function check_datetime(formatted_string) {
        var check_1 = formatted_string == '<div class="dt_cell">2017-04-20 15:09:56</div>';
        var check_2 = formatted_string == '<div class="dt_cell">2017-04-20 16:09:56</div>';
        return check_1 || check_2
    }

    assert.ok(check_datetime(string_formatter('Thu, 20 Apr 2017 15:09:56', {'type': 'datetime'}, row)));
    assert.ok(check_datetime(string_formatter('2017-04-20T15:09:56.013000', {'type': 'datetime'}, row)));
});


QUnit.test('threshold highlighting', function(assert) {
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
        string_formatter(4, {'min': {'field': 'nothere', 'default': 5}}, row),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    row = {'real_field': 5}
    assert.equal(
        string_formatter(4, {'min': {'field': 'real_field', 'default': 4}}, row),
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    assert.equal(
        string_formatter(6, {'min': {'field': 'real_field', 'default': 6}}, row),
        '<div class="dt_cell">6</div>'
    );
});


QUnit.test('arrays and links', function(assert) {
    assert.equal(
        string_formatter(['this', 'that'], {}, row),
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">that,this</div><div class="dropdown-content"><div>that</div><div>this</div></div></div></div>'
    );

    assert.equal(
        string_formatter(['a_page', 'another page'], {'link': '/to/'}, row),
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">a_page,another page</div><div class="dropdown-content"><div><a href="/to/a_page">a_page</a></div><div><a href="/to/another+page">another page</a></div></div></div></div>'
    );

    assert.equal(
        string_formatter(['a_page'], {'link': '/to/', 'link_format_function': 'count_entities'}, row),
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">1</div><div class="dropdown-content"><div><a href="/to/a_page">a_page</a></div></div></div></div>'
    );
});


QUnit.test('empty data', function(assert) {
    assert.equal(
        string_formatter([], {'type': 'float'}, row),
        '<div class="dt_cell"></div>'
    );

    assert.equal(
        string_formatter([], {'link_format_function': 'count_entities'}),
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">0</div></div></div>'
    );
});
