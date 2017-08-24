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


function format_link(data, fmt, formatted_link){
    if (fmt['postlink']){
        return '<a href=' + fmt['link'] + data + fmt['postlink'] + '>' + formatted_link + '</a>'
    }else{
        return '<a href=' + fmt['link'] + data + '>' + formatted_link + '</a>'
    }
}

function string_formatter(data, fmt){
    var formatted_data = data;

    if (fmt['type'] == 'percentage') {
        formatted_data = Humanize.toFixed(formatted_data, 1) + '%';
    }if (fmt['type'] == 'ratio_percentage') {
        formatted_data = Humanize.toFixed(formatted_data * 100, 1) + '%';
    } else if (fmt['type'] == 'int') {
        formatted_data = Humanize.intComma(formatted_data);
    } else if (fmt['type'] == 'float') {
        formatted_data = Humanize.formatNumber(formatted_data, 2);
    } else if (fmt['type'] == 'date') {
        formatted_data = moment(new Date(formatted_data)).format('YYYY-MM-DD');
    } else if (fmt['type'] == 'datetime') {
        formatted_data = moment(new Date(formatted_data)).format('YYYY-MM-DD HH:mm:ss');
    }
    if (fmt['link']) {
        if (fmt['link_format_function']){
            formatted_link = function_map[fmt['link_format_function']](data, fmt);
        }
        else{
            formatted_link = data;
        }
        // Multiple entries in the data or tooltip --> create drop down
        if (data instanceof Array && data.length > 1 || fmt['tooltip']) {
            data.sort();
            formatted_data = '<div class="dropdown"><div class="dropbtn">' + formatted_link + '</div><div class="dropdown-content">';
            for (var i=0, tot=data.length; i < tot; i++){
                formatted_data = formatted_data.concat(format_link(data[i], fmt, data[i]));
            }
            formatted_data = formatted_data.concat('</div></div>')
        }
        else if (data instanceof Array && data.length == 1){
            formatted_data = format_link(data[0], fmt, formatted_link);
        }
        else {
            formatted_data = format_link(data, fmt, formatted_link);
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

function count_entities_fmt(data, fmt){
    return data.length;
}

function coverage_15X_fmt(data, fmt){
    if ("bases_at_coverage" in data && "bases_at_15X" in data['bases_at_coverage'] && "genome_size" in data ) {
        return data['bases_at_coverage']['bases_at_15X']/data['genome_size']*100;
    }
}

function fastqc_report_fmt(data, fmt){
    return 'link';
}

var function_map = {
    'species_contamination': species_contamination_fmt,
    'count_entities': count_entities_fmt,
    'fastqc_report': fastqc_report_fmt,
    'coverage_15X': coverage_15X_fmt,
};
