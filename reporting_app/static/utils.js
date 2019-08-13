//helper function to retrieve a function by name
var get_function = function (fn_name){
    var fn = window[fn_name];
    if(typeof fn === 'function') {
        return fn;
    }else{
        return null;
    }
}

// Helper function to copy an object
function copy_obj(src) {
  var target = {};
  for (var prop in src) {
    if (src.hasOwnProperty(prop)) {
      target[prop] = src[prop];
    }
  }
  return target;
}

// ------------------------------ //
//   Merging datasets functions   //
// ------------------------------ //


var merge_on_key = function (list_of_array, key) {
    var r = [],
        hash = Object.create(null);

    list_of_array.forEach(function (a) {
        a.forEach(function (o) {
            if (!hash[o[key]]) {
                hash[o[key]] = {};
                r.push(hash[o[key]]);
            }
            Object.keys(o).forEach(function (k) {
                hash[o[key]][k] = o[k];
            });
        });
    });
    return r;
}

// merge several arrays of object based on given property but only keep object present in the first array
// the other ones can add properties but no new objects
var merge_on_key_keep_first_sub_properties = function (list_of_array, key, list_of_merge_property_names) {
    // Default list of property to empty array if it does not exist
    list_of_merge_property_names = list_of_merge_property_names || []

    var r = [];     // list of lists of objets to be flatten into a list of objects at the end.
    var hash = {};  // object that will ensure only the keys from the first list are kept

    // initialise the hash to only contain keys from the first list and the value are copies of the first list
    list_of_array[0].forEach(function (o) {
        if (o[key] in hash){
            hash[o[key]].push(copy_obj(o));
        }else{
            hash[o[key]] = [copy_obj(o)];
            // Store it in the final list
            r.push(hash[o[key]]);
        }
    });
    var i = 0;
    list_of_array.slice(1).forEach(function (a) {
        a.forEach(function (o) {
            if (hash[o[key]]) {
                hash[o[key]].forEach(function (k){
                    if (list_of_merge_property_names[i] == null ){
                        // Update the properties of k with o
                        Object.keys(o).forEach(function (j) {
                            k[j] = o[j];
                        });
                    } else {
                        k[list_of_merge_property_names[i]] = copy_obj(o)
                    }
                })
            }
        });
        i++;
    });
    //flatten the list of list
    return [].concat.apply([], r);
}

// Create a function that send multiple ajax queries then merge the results based using merge_func callback
// api_urls: [url1, url2, ...]
// token: the token used for authentication
// merging_key: property name to merge on
// func_name: the function used to merge the different results from the ajax calls.
var _merge_multi_sources = function(api_urls, token, merging_key, merge_func, merged_properties){
    return function(data, callback, settings){
        // Create a list of ajax calls
        var calls = api_urls.map( function(api_url){
            return $.ajax({
                url: api_url,
                headers: {'Authorization':  token },
                dataType: 'json',
                async: true,
            });
        });

        // pass an array of deferred calls and apply with Function.prototype.apply
        // see http://stackoverflow.com/questions/5627284/pass-in-an-array-of-deferreds-to-when
        $.when.apply($, calls).then(function () {
            // Use 'arguments' to get all the responses as an array-like object.
            // then extract the data field
            var data_array = _.map(arguments, function(response){return response[0].data});
            var result = merge_func(data_array, merging_key, merged_properties);
            callback({
                recordsTotal: result.length,
                recordsFiltered: result.length,
                data: result
            });
        });
    }
}

// Create a function that send multiple ajax queries then merge the results keeping all entries (outer join)
// api_urls: [url1, url2, ...]
// token: the token used for authentication
// merging_key: property name to merge on
var merge_multi_sources = function(api_urls, token, merging_key){
    return _merge_multi_sources(api_urls, token, merging_key, merge_on_key);
}

// Create a function that send multiple ajax queries then merge the results keeping entries form the first (left inner join)
// api_urls: [url1, url2, ...]
// token: the token used for authentication
// merging_key: property name to merge on
var merge_multi_sources_keep_first = function(api_urls, token, merging_key, merged_properties){
    return _merge_multi_sources(api_urls, token, merging_key, merge_on_key_keep_first_sub_properties, merged_properties);
}

// Create a function that will query the Lims endpoint for a single container,
// then it will retrieve all sample_id and make a query to the qc_url the results will me merged on sample_id.
function merge_lims_container_and_qc_data(lims_url, qc_url, token) {
    return function(data, callback, settings){
        $.ajax(
        {
            url: lims_url,
            headers: {'Authorization': token},
            dataType: 'json',
            success: function(result) {
                var merged_results = result.data;

                var sample_queries = [];  // sample IDs to merge on
                var sample_coords = {};  // map sample IDs to index of the sample in merged_results so we can merge the sequencing qc later
                merged_results.forEach(function(sample, i){
                    var sample_id = sample['name'];
                    sample_coords[sample_id] = i;
                    sample_queries.push('{"sample_id":"' + sample_id + '"}');
                });
                // query the samples endpoint for IDs found above, merge in the data and trigger the chart
                $.ajax(
                    {
                        url: qc_url + '?where={"$or":[' + sample_queries.join(',') + ']}&max_results=1000',
                        headers: {'Authorization': token},
                        dataType: 'json',
                        success: function(result) {
                            _.forEach(result.data, function(sample_qc) {
                                var i = sample_coords[sample_qc['sample_id']];
                                merged_results[i]['bioinformatics_qc'] = sample_qc;
                            });
                            callback({
                                recordsTotal: merged_results.length,
                                recordsFiltered: merged_results.length,
                                data: merged_results
                            });
                        }
                    }
                );
            }
        }
    );
    }
}


// Check that the variable exists, is not null
// If it is an array, check that it is not empty or only containing null values
var test_exist = function(variable){
    if ( variable instanceof Array ) {
        variable = variable.filter(function(n){ return n != null });
        return variable.length > 0;
    }
    return variable !== undefined && variable !== null && variable;
}

// Calculate the number of significant decimal digits to show from a range of number.
var significant_figures = function(array_of_number){
    if (_.every(array_of_number, Number.isInteger)){
        return 0;
    }
    // spread operator does not work with phantomJS
    var span = Math.max.apply(Math, array_of_number) - Math.min.apply(Math, array_of_number);

    var sig_fig = 0
    if (span < .1) {
        sig_fig = 4
    }else if (span < 1) {
        sig_fig = 3
    }else if (span < 10) {
        sig_fig = 2
    }else if (span < 100) {
        sig_fig = 1
    }
    return sig_fig
}

//get any percentile from an array
var getPercentile = function(data, percentile) {
    //because .sort() doesn't sort numbers correctly
    data.sort(function(a, b){ return a - b });
    var index = (percentile / 100) * data.length;
    var result;
    if (Math.floor(index) == index) {
        result = (data[(index - 1)] + data[index]) / 2;
    } else {
        result = data[Math.floor(index)];
    }
    return result;
}


function aggregate(list_object, toGroup, toAggregate, fn, output_field, val0) {
    /*
    Use lodash.js to group, and aggregate the data provided in the list_object.
    The list of object will be group on a field and one or multiple aggregation function will be applied to one or
    multiple other fields.
    Parameter toAggregate, fn and output_field should be of the same type and have te same length if they are arrays.

    list_object: list of object to aggregate
    toGroup: field used to group the object
    toAggregate: field or list of field to aggregate and report after grouping
    fn: function or list of function to calculate the aggregate
    output_field: field or list of field to name the aggregated fields default to toAggregate
    val0: value of list of value used as default for each field.
    */
    if (output_field === undefined){output_field=toAggregate;}
    return _.chain(list_object)
            .groupBy(toGroup)
            .map(function(g, key) {
                ret = {}
                // Because the key has been used as an object property, it has been cast to a string.
                ret[toGroup] = key;
                if (Array.isArray(toAggregate)){
                    for (var i=0; i < toAggregate.length; i++) {
                        // Filter out null values
                        var fg = _.filter(g, function(e){return _.get(e, toAggregate[i]) != null })
                        ret[output_field[i]] = fn[i](fg,  toAggregate[i]) || val0[i];
                    }
                }else{
                    // Filter out null values
                    var fg = _.filter(g, function(e){return _.get(e, toAggregate) != null })
                    ret[output_field] = fn(fg, toAggregate) || val0;
                }
                return ret;
            })
            .value();
    }

/*Functions for aggregation in the underscore pipeline*/
var sum = function (objects, key) { return _.reduce(objects, function (sum, n) { return sum + _.get(n, key) }, 0) }
var average = function (objects, key) {return sum(objects, key) / objects.length }
var count = function (objects, key) { return objects.length }
var extract = function (objects, key) { return objects.map( function(d){ return _.get(d, key);  }); }
var quantile_box_plot = function (objects, key) {
    // Provide 5, 25, 50, 75, and 95 percentile from a list of objects and a key
    return math.quantileSeq(objects.map(function(d){return _.get(d, key)}), [0.05, .25, .5, .75, 0.95]);
}
var boxplot_values_outliers = function(objects, key) {
    // This function returns an object containing standard values for a box plot
    // The 25, 50, and 75 percentile for the box
    // 1.5 time inter-quartile for the top and bottom whiskers
    // It also extract all the point that falls out of the whiskers and report them as outliers
    var data = extract(objects, key);
    var boxData = {},
        min = Math.min.apply(Math, data),
        max = Math.max.apply(Math, data),
        q1 = getPercentile(data, 25),
        median = getPercentile(data, 50),
        q3 = getPercentile(data, 75),
        iqr = q3 - q1,
        lowerFence = q1 - (iqr * 1.5),
        upperFence = q3 + (iqr * 1.5),
        outliers = [];
        in_dist_data = [];

    for (var i = 0; i < data.length; i++) {
        if (data[i] < lowerFence || data[i] > upperFence) {
            outliers.push(data[i]);
        }else{
            in_dist_data.push(data[i])
        }
    }
    boxData.values = [Math.min.apply(Math, in_dist_data), q1, median, q3, Math.max.apply(Math, in_dist_data)];
    boxData.outliers = outliers;
    return boxData;
}

/*Function for formatting tooltip text from a time data point*/
function format_time_period(time_period, x) {
    if (time_period=='date'){return moment(x).format("DD MMM YYYY");}
    if (time_period=='week'){return 'Week ' + moment(x).format("w YYYY");}
    if (time_period=='month'){return moment(x).format("MMM YYYY");}
    if (time_period=='quarter'){return 'Q' + moment(x).format("Q YYYY");}
    return ""
}

function format_y_point(y, prefix, suffix, nb_decimal){return prefix + ' ' + y.toFixed(nb_decimal) + ' ' + suffix}
function format_y_boxplot(options, prefix, suffix, nb_decimal){
    res = [
       'low: ' + prefix + ' ' + options.low.toFixed(nb_decimal) + ' ' + suffix,
       '25pc: ' + prefix + ' '  + options.q1.toFixed(nb_decimal) + ' ' + suffix,
       'Median: ' + prefix + ' '  + options.median.toFixed(nb_decimal) + ' ' + suffix,
       '75pc: ' + prefix + ' '  + options.q3.toFixed(nb_decimal) + ' ' + suffix,
       'high: ' + prefix + ' '  + options.high.toFixed(nb_decimal) + ' ' + suffix
    ]
    return res.join('<br>');
}
function format_point_tooltip(series_name, x, y, time_period, prefix,  suffix, nb_decimal){
    return  series_name + " --  " + format_time_period(time_period, x) + ": <br> " + format_y_point(y, prefix, suffix, nb_decimal);
}
    function format_boxplot_tooltip(series_name, x, options, time_period, prefix, suffix, nb_decimal) {
    return series_name +
           " -- " +
           format_time_period(time_period, x) +
           ": <br> " +
           format_y_boxplot(options, prefix, suffix, nb_decimal);
}


