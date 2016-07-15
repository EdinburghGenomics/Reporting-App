/**
 * Author: mwhamgenomics
 * @module column_formatter.js
 */

function render_data(data, type, row, meta, fmt) {
    if (!data && data !== 0) {
        return null;
    }
    if (!fmt) {
        return '<div class="dt_cell">' + data + '</div>';
    }
    if (fmt['name']) {
        data = function_map[fmt['name']](data, fmt)
    }
    return string_formatter(data, fmt)
}


function string_formatter(data, fmt){
    var formatted_data = data;

    if (fmt['type'] == 'percentage') {
        formatted_data = Humanize.toFixed(formatted_data, 1) + '%';
    } else if (fmt['type'] == 'int') {
        formatted_data = Humanize.intComma(formatted_data);
    } else if (fmt['type'] == 'float') {
        formatted_data = Humanize.formatNumber(formatted_data, 2);
    }

    if (fmt['link']) {
        if (data instanceof Array && data.length > 1) {
            formatted_data = '<div class="dropdown"><div class="dropbtn">' + data + '</div><div class="dropdown-content">';
            for (var i=0, tot=data.length; i < tot; i++){
                formatted_data = formatted_data.concat('<a href=' + fmt['link'] + data[i] + '>' + data[i] + '</a>');
            }
            formatted_data = formatted_data.concat('</div></div>')
        }
        else if (data instanceof Array && data.length == 1){
            formatted_data = '<a href=' + fmt['link'] + data[0] + '>' + data[0] + '</a>';
        }
        else {
            formatted_data = '<a href=' + fmt['link'] + data + '>' + data + '</a>';
        }
    }
    if (fmt['min'] && data < fmt['min']) {
        formatted_data = '<div style="color:red">' + formatted_data + '</div>';
    } else if (fmt['max'] && data > fmt['max']) {
        formatted_data = '<div style="color:red">' + formatted_data + '</div>';
    }

    formatted_data = '<div class="dt_cell">' + formatted_data + '</div>';
    return formatted_data;
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

var function_map = {
    'species_contamination': species_contamination_fmt
};