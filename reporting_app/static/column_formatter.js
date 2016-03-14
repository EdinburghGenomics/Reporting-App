/**
 * Author: mwhamgenomics
 * @module column_formatter.js
 */

function render_data(data, fmt) {
    if (!data) {
        return null;
    }
    if (!fmt) {
        return data;
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
        if (data instanceof Array){
        formatted_data = "";
            for (var i=0,  tot=data.length; i < tot; i++){
                formatted_data = formatted_data.concat(' <a href=' + fmt['link'] + data[i] + '>' + data[i] + '</a>')
            }
        }
        else{
            formatted_data = '<a href=' + fmt['link'] + data + '>' + data + '</a>'
        }
    }
    if (fmt['min'] && data < fmt['min']) {
        formatted_data = '<p style="color:red">' + formatted_data + '</p>';
    }

    return formatted_data;
}

