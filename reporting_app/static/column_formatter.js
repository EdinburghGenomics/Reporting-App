
function render_data(data, fmt) {
    if (!fmt) {
        return data;
    }

    if (fmt['type'] == 'percentage') {
        return Humanize.toFixed(data, 1) + '%';
    } else if (fmt['type'] == 'largeint') {
        return Humanize.intComma(data);
    } else if (fmt['type'] == 'largefloat') {
        return Humanize.formatNumber(data, 2);
    } else {
        return data;
    }
}

