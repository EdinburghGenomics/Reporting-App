/**
 * Author: mwhamgenomics
 * @module column_formatter.js
 */

function render_data(data, fmt) {
    if (!data) {
        return null;
    }
    if (!fmt) {
        return '<div class="dt_cell">' + data + '</div>';
    }
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
        formatted_data = '<p style="color:red">' + formatted_data + '</p>';
    }

    formatted_data = '<div class="dt_cell">' + formatted_data + '</div>';
    return formatted_data;
}

