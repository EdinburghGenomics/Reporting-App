/**
 * Author: mwhamgenomics
 * @module column_formatter.js
 */

function render_data(data, type, row, meta, fmt) {
    if (!data && data !== 0) {
        return null;
    }
    if (!fmt) {
        fmt = {};
    }
    if (fmt['name']) {
        data = function_map[fmt['name']](data, fmt)
    }
    return string_formatter(data, fmt, row)
}


function string_formatter(cell_data, fmt, row){
    // cast the cell data to a list, whether it's a single value, an object or already a list
    // this allows subsequent logic to safely assume it's handling a list
    if (cell_data instanceof Array) {
        cell_data.sort();
    } else if (cell_data instanceof Object) {
        // convert, e.g, {'this': 0, 'that': 1, 'other': 2} to ['this: 0', 'that: 1', 'other: 2']
        var _cell_data = [];
        for (k in cell_data) {
            _cell_data.push(k + ': ' + cell_data[k]);
        }
        cell_data = _cell_data;
    } else {
        cell_data = [cell_data];  // cast a single value to a list of length 1
    }

    var formatted_data = [];
    for (var i=0, tot=cell_data.length; i<tot; i++) {
        var data = cell_data[i];
        var _formatted_data;

        if (fmt['type'] == 'percentage') {
            _formatted_data = Humanize.toFixed(data, 1) + '%';
        } else if (fmt['type'] == 'ratio_percentage') {
            _formatted_data = Humanize.toFixed(data * 100, 1) + '%';
        } else if (fmt['type'] == 'int') {
            _formatted_data = Humanize.intComma(data);
        } else if (fmt['type'] == 'float') {
            _formatted_data = Humanize.formatNumber(data, 2);
        } else if (fmt['type'] == 'date') {
            _formatted_data = moment(new Date(data)).format('YYYY-MM-DD');
        } else if (fmt['type'] == 'datetime') {
            _formatted_data = moment(new Date(data)).format('YYYY-MM-DD HH:mm:ss');
        } else {
            _formatted_data = data;
        }

        if (fmt['link']) {  // convert the link to an html <a/>, replacing ' ' with '+'
            _formatted_data = '<a href=' + fmt['link'] + data.replace(/ /g, "+") + '>' + data + '</a>';
        }

        var min, max;
        if (fmt['min']) {
            min = resolve_min_max_value(row, fmt['min'])
        }
        if (fmt['max']) {
            max = resolve_min_max_value(row, fmt['max'])
        }
        if (min && data < min) {
            _formatted_data = '<div style="color:red">' + _formatted_data + '</div>';
        } else if (max && !isNaN(max) && data > max) {
            _formatted_data = '<div style="color:red">' + _formatted_data + '</div>';
        } else if (max && data > max) {
            _formatted_data = '<div style="color:red">' + _formatted_data + '</div>';
        }

        formatted_data.push(_formatted_data);

    }

    // if the list is longer than 1, then it should be rendered as a dropdown
    if (formatted_data.length > 1) {
        // build a <div class="dropdown"><div class="dropbtn">text or link</div></div>
        var dropdown = document.createElement('div');
        dropdown.className = 'dropdown';

        var dropbtn = document.createElement('div');
        dropbtn.className = 'dropbtn';
        if (fmt['link_format_function']) {
            dropbtn.innerHTML = function_map[fmt['link_format_function']](cell_data, fmt);
        } else {
            dropbtn.innerHTML = cell_data;
        }

        var dropdown_content = document.createElement('div');
        dropdown_content.className = 'dropdown-content';

        var div;
        for (var i=0, tot=formatted_data.length; i<tot; i++) {
            div = document.createElement('div');
            div.innerHTML = formatted_data[i];
            dropdown_content.appendChild(div);
        }

        dropdown.appendChild(dropbtn);
        dropdown.appendChild(dropdown_content);
        formatted_data = dropdown.outerHTML;
    } else {
        formatted_data = formatted_data[0];
    }

    return '<div class="dt_cell">' + formatted_data + '</div>';
}


function resolve_min_max_value(row, value){
    // find the value in row or return the original value;
    if (typeof value === 'object'){
        // object should be {field: "field_name", default: default_value}
        if (value['field'] in row){
            return row[value['field']];
        } else {
            return value['default'];
        }
    }
    else if (value in row){
        // If the value is in the row then it is field name
        return row[value];
    }
    // Otherwise it is just a value
    return value;
}

function merge_column(data, row){
    return data + '-' + row[1]
}

function species_contamination_fmt(data, fmt){
    var best_species = [];
    for (var species in data['contaminant_unique_mapped']){
        if (data['contaminant_unique_mapped'][species] > 500){
            best_species.push(species)
        }
    }
    return best_species.join()
}

function count_entities_fmt(data, fmt){
    return data.length;
}

function coverage_fmt(data, fmt, bases_at_X){
    if ("bases_at_coverage" in data && bases_at_X in data['bases_at_coverage'] && "genome_size" in data ) {
        return data['bases_at_coverage'][bases_at_X]/data['genome_size']*100;
    }
}

function coverage_15X_fmt(data, fmt){
    return coverage_fmt(data, fmt, 'bases_at_15X')
}

function coverage_5X_fmt(data, fmt){
    return coverage_fmt(data, fmt, 'bases_at_5X')
}


var function_map = {
    'species_contamination': species_contamination_fmt,
    'count_entities': count_entities_fmt,
    'coverage_15X': coverage_15X_fmt,
    'coverage_5X': coverage_5X_fmt
};
