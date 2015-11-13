
function render_data(data, fmt) {
    if (!fmt) {
        return data;
    }
    if (fmt['commas']) {
        return Humanize.formatNumber(data, 2);
    } else if (fmt['percentage']) {
        return Humanize.formatNumber(data, 1) + '%';
    } else {
        return data;
    }
}

