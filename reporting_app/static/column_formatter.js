
function render_data(data, fmt) {
    if (!data) {
        return null;
    }
    if (!fmt) {
        return data;
    }

    if (fmt['type'] == 'percentage') {
        data = Humanize.toFixed(data, 1) + '%';
    } else if (fmt['type'] == 'largeint') {
        data = Humanize.intComma(data);
    } else if (fmt['type'] == 'largefloat') {
        data = Humanize.formatNumber(data, 2);
    }

    if (fmt['min'] && data < fmt['min']) {
            data = '<p style="color:red">' + data + '</p>';
    }

    return data;

}

