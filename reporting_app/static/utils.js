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
var merge_on_key_keep_first_sub_porperties = function (list_of_array, key, list_of_merge_property_names) {
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
    return r.flat(1);
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
    return _merge_multi_sources(api_urls, token, merging_key, merge_on_key_keep_first_sub_porperties, merged_properties);
}

var test_exist = function(variable){
    if ( variable instanceof Array ) {
        variable = variable.filter(function(n){ return n != null });
        return variable.length > 0;
    }
    return variable !== undefined && variable !== null && variable;
}
