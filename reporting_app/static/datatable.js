//helper function to retrieve a function by name
var get_function = function (fn_name){
    var fn = window[fn_name];
    if(typeof fn === 'function') {
        return fn;
    }else{
        return null;
    }
}


// merge several arrays of object based on given property
// see http://stackoverflow.com/questions/38053193/merge-2-json-array-objects-based-on-a-common-property
var merge_on = function (list_of_array, key) {
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
var merge_on_keep_first = function (list_of_array, key) {
    var r = [],
        hash = Object.create(null);

    list_of_array[0].forEach(function (o) {
        hash[o[key]] = {};
        r.push(hash[o[key]]);
    });
    list_of_array.forEach(function (a) {
        a.forEach(function (o) {
            if (hash[o[key]]) {
                Object.keys(o).forEach(function (k) {
                    hash[o[key]][k] = o[k];
                });
            }
        });
    });
    return r;
}

// send multiple ajax queries then merge the results based on dt_config.merge_on
// dt_config is expected to contain:
// ajax_call.func_name: merge_multi_sources,
// ajax_call.api_urls: [url1, url2, ...]
// ajax_call.merge_on: property_name
// token: the token used for authentication
var _merge_multi_sources = function(dt_config, merge_func){
    return function(data, callback, settings){
        var calls = dt_config.ajax_call.api_urls.map( function(api_url){
            return  $.ajax({
                url: api_url,
                headers: {'Authorization':  dt_config.token },
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
            var result = merge_func(data_array, dt_config.ajax_call.merge_on);
            callback({
                recordsTotal: result.length,
                recordsFiltered: result.length,
                data: result
            });
        });
    }
}

var merge_multi_sources = function(dt_config){
    return _merge_multi_sources(dt_config, merge_on);
}

var merge_multi_sources_keep_first = function(dt_config){
    return _merge_multi_sources(dt_config, merge_on_keep_first);
}

var test_exist = function(variable){
    if ( variable instanceof Array ) {
        return variable.length > 0;
    }
    return variable !== undefined;
}

var color_filter = function( row, data, dataIndex ) {
    if ( test_exist(data["trim_r1"]) || test_exist(data["trim_r2"]) || test_exist(data["tiles_filtered"]) ) {
          $(row).addClass('data-filtering');
    }
}

function create_datatable(dt_config){
    //Sets default value using Lodash.js
    _.defaults(dt_config, {'buttons': 'defaults'});
    $(document).ready(function(){
        var table = $('#' + dt_config.name).DataTable(configure_dt(dt_config));
        if (dt_config.buttons){
            new $.fn.dataTable.Buttons(table, {'buttons': configure_buttons(dt_config.buttons)});
            table.buttons().container().prependTo(table.table().container());
        }
    });
}


// Configure the buttons for datatable
var configure_buttons = function(button_config){
    var buttons_def = {
        'colvis': {extend: 'colvis', text: '<i class="fa fa-filter"></i>',     titleAttr: 'Filter Columns'},
        'copy': {extend: 'copy',   text: '<i class="fa fa-files-o"></i>',    titleAttr: 'Copy', exportOptions: {'columns': ':visible'} },
        'pdf': {extend: 'pdf',    text: '<i class="fa fa-file-pdf-o"></i>', titleAttr: 'PDF', orientation: 'landscape', exportOptions: {'columns': ':visible'}}
    }
    if (button_config === 'defaults'){
        button_config = ['colvis', 'copy', 'pdf']
    }
    return button_config.map(function(n){return buttons_def[n]});
}


// Configure datatable
var configure_dt = function(dt_config) {
    //Sets default value using Lodash.js
    _.defaults(dt_config, {
        'fixed_header': false,
        'paging': true,
        'searching': true,
        'info': true,
    });
    // configure the ajax call or retrieve the ajax callback function
    var ajax_call = {
        'url': dt_config.api_url,
        'dataSrc': 'data',
        'headers': {'Authorization': dt_config.token}
    }
    if (dt_config.ajax_call){
        // retrieve the function generating the ajax calls by name and call it with the config
        ajax_call = get_function(dt_config.ajax_call.func_name)(dt_config);
    }
    return {
        'dt_config': dt_config,
        'fixedHeader': dt_config.fixed_header,
        'paging': dt_config.paging,
        'searching': dt_config.searching,
        'info': dt_config.info,
        'processing': true,
        'serverSide': false,
        'autoWidth': false,
        //'stateSave': true,
        'lengthMenu': [[10, 25, 50, -1], [10, 25, 50, "All"]],
        'pageLength': 25,
        'ajax': ajax_call,
        'language': {'processing': '<i class="fa fa-refresh fa-spin">'},
        'columns': dt_config.cols.map(
            function(c) {
                return {
                    'data': c.data,
                    'name': c.data,
                    'render': function(data, type, row, meta) {
                        return render_data(data, type, row, meta, c.fmt)
                    },
                    'orderable': !c.orderable || String(c.orderable).toLowerCase() == 'true',
                    'visible': !c.visible || String(c.visible).toLowerCase() == 'true',
                    'defaultContent': '',
                    'width': c.width || '10%',
                    'className': c.class_name
                };
            }
        ),
        'order': [dt_config.default_sort_col],
        'footerCallback': get_function(dt_config.table_foot),
        "createdRow": get_function(dt_config.create_row)
    }
}

// Helper function that sums the value of a column
var sum_row_per_column = function( row, data, start, end, display ) {
    // sum up the column with a class sum into the footer
    var api = this.api();
    // Total over current page
    api.columns('.sum', { page: 'current' }).every(function () {
        var sum = this
                .cells( null, this.index(), { page: 'current'} )
                .data()
                .reduce(function (a, b) {
                    if (b.constructor === Array){
                        return a + b.length;
                    }else if (!isNaN(parseFloat(b)) && isFinite(b)){
                        return a + parseFloat(b);
                    }else if (b === ''){
                        return a;
                    }else{
                        return Number.NaN;
                    }
                }, 0);
        // Update footer
        if (isNaN(sum) ){
            $(this.footer()).html( '' );
        }else{
            $(this.footer()).html( sum );
        }
    });

}
