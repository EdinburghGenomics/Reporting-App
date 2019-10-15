import {
    string_formatter, resolve_min_max_value, species_contamination_fmt, coverage_fmt, pipeline_used_fmt
} from '../../reporting_app/src/column_formatter.js';


var row = {};


test('number formatting', function() {
    expect(string_formatter(13.37, {'type': 'percentage'}, row)).toBe(
        '<div class="dt_cell">13.4%</div>'
    );

    expect(string_formatter(0.1337, {'type': 'ratio_percentage'}, row)).toBe(
        '<div class="dt_cell">13.4%</div>'
    );

    expect(string_formatter(1337, {'type': 'int'}, row)).toBe(
        '<div class="dt_cell">1,337</div>'
    );

    expect(string_formatter(1.337, {'type': 'float'}, row)).toBe(
        '<div class="dt_cell">1.34</div>'
    );
});


test('date formatting', function() {
    expect(string_formatter('Thu, 20 Apr 2017 15:09:56 GMT', {'type': 'date'}, row)).toBe(
        '<div class="dt_cell">2017-04-20</div>'
    );

    expect(string_formatter('2017-04-20T15:09:56.013000Z', {'type': 'date'}, row)).toBe(
        '<div class="dt_cell">2017-04-20</div>'
    );

    // I hate MomentJS.
    function check_datetime(formatted_string) {
        var check_1 = formatted_string == '<div class="dt_cell">2017-04-20 15:09:56</div>';
        var check_2 = formatted_string == '<div class="dt_cell">2017-04-20 16:09:56</div>';
        return check_1 || check_2
    }

    expect(check_datetime(string_formatter('Thu, 20 Apr 2017 15:09:56', {'type': 'datetime'}, row))).toBe(true);
    expect(check_datetime(string_formatter('2017-04-20T15:09:56.013000', {'type': 'datetime'}, row))).toBe(true);
});


test('threshold highlighting', function() {
    // 1-3 inclusive are normal
    expect(string_formatter(1, {'min': 1, 'max': 3}, row)).toBe(
        '<div class="dt_cell">1</div>'
    );
    expect(string_formatter(3, {'min': 1, 'max': 3}, row)).toBe(
        '<div class="dt_cell">3</div>'
    );

    // anything outside 1-3 is highlighted red
    expect(string_formatter(0, {'min': 1, 'max': 3}, row)).toBe(
        '<div class="dt_cell"><div style="color:red">0</div></div>'
    );
    expect(string_formatter(4, {'min': 1, 'max': 3}, row)).toBe(
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    // required_yield not present in row, but min defaults to 5 so highlight 4 in red
    expect(string_formatter(4, {'min': {'field': 'required_yield', 'default': 5}}, row)).toBe(
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );

    // when required_yield is present, treat as normal min/max
    var populated_row = {'required_yield': 5};
    expect(string_formatter(4, {'min': {'field': 'required_yield', 'default': 4}}, populated_row)).toBe(
        '<div class="dt_cell"><div style="color:red">4</div></div>'
    );
    expect(string_formatter(6, {'min': {'field': 'required_yield', 'default': 6}}, populated_row)).toBe(
        '<div class="dt_cell">6</div>'
    );
});


test('arrays and links', function() {
    expect(string_formatter(['this', 'that'], {}, row)).toBe(
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">that,this</div><div class="dropdown-content"><div>that</div><div>this</div></div></div></div>'
    );

    expect(string_formatter(['a_page', 'another page'], {'link': '/to/'}, row)).toBe(
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">a_page,another page</div><div class="dropdown-content"><div><a href="/to/a_page">a_page</a></div><div><a href="/to/another+page">another page</a></div></div></div></div>'
    );

    expect(string_formatter(['a_page'], {'link': '/to/', 'link_format_function': 'count_entities'}, row)).toBe(
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">1</div><div class="dropdown-content"><div><a href="/to/a_page">a_page</a></div></div></div></div>'
    );
});


test('empty data', function() {
    expect(string_formatter([], {'type': 'float'}, row)).toBe(
        '<div class="dt_cell"></div>'
    );

    // empty dropdown with '0' as displayed total
    expect(string_formatter([], {'link_format_function': 'count_entities'}, row)).toBe(
        '<div class="dt_cell"><div class="dropdown"><div class="dropbtn">0</div></div></div>'
    );
});


test('resolve_min_max_value', function() {
    var row = {'x': 1, 'y': 2};

    expect(resolve_min_max_value(row, {'field': 'z', 'default': 4})).toBe(  // z not present, so default to 4
        4
    );

    expect(resolve_min_max_value(row, {'field': 'y', 'default': 4})).toBe(  // y present, so override default
        2
    );

    expect(resolve_min_max_value(row, 'y')).toBe(  // simple referencing
        2
    );

    // simple referencing for a non-existing key just spits back the key
    expect(resolve_min_max_value(row, 'z')).toBe(
        'z'
    );
});


test('species_contamination_fmt', function() {
    expect(
        species_contamination_fmt(
            {'contaminant_unique_mapped': {'Thingius thingy': 501, 'Thangius thangy': 499, 'Homo sapiens': 1000}},
                null
        )
    ).toBe('Thingius thingy,Homo sapiens');
});


test('coverage_fmt', function() {
    expect(coverage_fmt({'bases_at_coverage': {'bases_at_15X': 1337}, 'genome_size': 1000}, null, 'bases_at_15X')).toBe(
        133.7
    );

    expect(coverage_fmt({}, null, 'bases_at_15X')).toBeUndefined();
});


test('pipeline_used_fmt', function() {
    expect(pipeline_used_fmt({'name': 'a_pipeline', 'toolset_type': 'a_toolset', 'toolset_version': 1}, null)).toBe(
        'a_pipeline (a_toolset v1)'
    );
});
