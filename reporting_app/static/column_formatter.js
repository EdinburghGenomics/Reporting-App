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


function flatten_object(cell_object){
    // convert, e.g, {'this': 0, 'that': 1, 'other': 2} to ['other: 2', 'that: 1', 'this: 0']
    var cell_array = [];
    var keys = Object.keys(cell_object);
    keys.sort();

    var i;
    var nkeys = keys.length;
    for (i=0; i<nkeys; i++) {
        var k = keys[i];
        cell_array.push(k + ': ' + cell_object[k]);
    }
    return cell_array
}

function get_samples(cell_object){
    return cell_object['samples']
}

function string_formatter(cell_data, fmt, row){
    original_cell_data = cell_data;
    // cast the cell data to a list, whether it's a single value, an object or already a list
    // this allows subsequent logic to safely assume it's handling a list
    if (cell_data instanceof Array) {
        cell_data.sort();
    } else if (cell_data instanceof Object) {
        if ('object_converter' in fmt){
            cell_data = function_map[fmt['object_converter']](cell_data)
            cell_data.sort()
        }else{
            cell_data = flatten_object(cell_data)
        }
    } else {
        cell_data = [cell_data];  // cast a single value to a list of length 1
    }

    // Only arrays
    var formatted_data = [];
    var i, tot;
    for (i=0, tot=cell_data.length; i<tot; i++) {
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

    // if the list is longer than 1 or if it has special formatting, then it should be rendered as a dropdown
    if (formatted_data.length > 1 || fmt['link_format_function']) {
        // build a <div class="dropdown"><div class="dropbtn">text or link</div></div>
        var dropdown = document.createElement('div');
        dropdown.className = 'dropdown';

        var dropbtn = document.createElement('div');
        dropbtn.className = 'dropbtn';

        if (fmt['link_format_function']) {
            dropbtn.innerHTML = function_map[fmt['link_format_function']](formatted_data, fmt);
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
        if (formatted_data.length) {
            dropdown.appendChild(dropdown_content);
        }
        formatted_data = dropdown.outerHTML;
    } else if (formatted_data.length == 1) {
        formatted_data = formatted_data[0];
    }

     var dt_cell = document.createElement('div');
     dt_cell.className = 'dt_cell';
    // Applying cell formatting, if specified.
    if (fmt['cell_format_function']) {
        style_list = function_map[fmt['cell_format_function']](original_cell_data, fmt);
        if (style_list != null){
            dt_cell.setAttribute("style", "background-color:" + style_list[0] + ";color:hsla(" + style_list[1] + ")");
        }
    }
    dt_cell.innerHTML = formatted_data
    return dt_cell.outerHTML;
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
    if ('samples' in data) {
        return data['samples'].length;
    }
    return data.length;
}

function temporal_fmt(cell_data, fmt){
/*
 * Returns formatting style is for project status page, displaying a green, yellow or red if it is over a week,
 * two weeks or four weeks since the last change. Colour selection from https://clrs.cc/
 */
    // Checking staleness of the status' max date
    status_date = new Date(cell_data['last_modified_date']);
    // Creating fixed date variable to compare against
    week_ago = new Date();
    week_ago.setDate(week_ago.getDate() - 7)
    two_weeks_ago = new Date();
    two_weeks_ago.setDate(week_ago.getDate() - 14)
    four_weeks_ago = new Date();
    four_weeks_ago.setDate(week_ago.getDate() - 28)

    if ( status_date < four_weeks_ago ){
        return ["#2ECC40", "127, 63%, 15%, 1.0"]
    }
    else if ( status_date < two_weeks_ago ){
        return ["#FFDC00", "52, 100%, 20%, 1.0"]
    }
    else if ( status_date < week_ago ){
        return ["#FF4136", "3, 100%, 25%, 1.0"]
    }
}

function coverage_fmt(data, fmt, bases_at_X){
    if ('bases_at_coverage' in data && bases_at_X in data['bases_at_coverage'] && 'genome_size' in data ) {
        return data['bases_at_coverage'][bases_at_X]/data['genome_size']*100;
    }
}

function coverage_15X_fmt(data, fmt){
    return coverage_fmt(data, fmt, 'bases_at_15X')
}

function coverage_5X_fmt(data, fmt){
    return coverage_fmt(data, fmt, 'bases_at_5X')
}


function pipeline_used_fmt(data, fmt) {
    return data['name'] + ' (' + data['toolset_type'] + ' v' + data['toolset_version'] + ')'
}


var function_map = {
    'species_contamination': species_contamination_fmt,
    'count_entities': count_entities_fmt,
    'temporal': temporal_fmt,
    'coverage_15X': coverage_15X_fmt,
    'coverage_5X': coverage_5X_fmt,
    'pipeline_used': pipeline_used_fmt,
    'get_samples': get_samples
};
