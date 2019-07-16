// datatables specific functions for merge_multi_sources and merge_multi_sources_keep_first
var dt_merge_multi_sources = function(dt_config){
    return merge_multi_sources(
        dt_config.ajax_call.api_urls,
        dt_config.token,
        dt_config.ajax_call.merge_on,
        dt_config.ajax_call.merged_properties
    );
}

var dt_merge_multi_sources_keep_first = function(dt_config){
    return merge_multi_sources_keep_first(
        dt_config.ajax_call.api_urls,
        dt_config.token,
        dt_config.ajax_call.merge_on,
        dt_config.ajax_call.merged_properties
    );
}

var required_yields = function(dt_config) {
    return function(data, callback, settings) {
        var response;
        $.ajax(
            {
                url: dt_config.ajax_call.api_url,
                headers: {'Authorization': dt_config.token},
                dataType: 'json',
                async: false,
                success: function(result) { response = result; }
            }
        );
        var d = response.data;

        if (d.length > 1) {
            console.warn('data is not of length 1');
        }

        var aggregated_data = d[0]['aggregated'];
        var result = [];

        for (k in aggregated_data['required_yield']) {
            result.push(
                {
                    'coverage': {'order': k.slice(0, -1), 'disp': k},
                    'required_yield': aggregated_data['required_yield'][k],
                    'required_yield_q30': aggregated_data['required_yield_q30'][k]
                }
            )
        };

        callback({
            recordsTotal: result.length,
            recordsFiltered: result.length,
            data: result
        });
    }
}


var test_exist = function(variable){
    if ( variable instanceof Array ) {
        variable = variable.filter(function(n){ return n != null });
        return variable.length > 0;
    }
    return variable !== undefined && variable !== null && variable;
}

var color_filter = function( row, data, dataIndex ) {
    if (test_exist(data['trim_r1']) || test_exist(data['trim_r2']) || test_exist(data['tiles_filtered'])) {
          $(row).addClass('data-filtering');
    }
}

var color_data_source = function( row, data, dataIndex ) {
    if (
        _.has(data, 'aggregated.most_recent_proc.data_source')
        && _.has(data, 'aggregated.from_run_elements.useable_run_elements')
    ) {
        var list1 = _.get(data, 'aggregated.from_run_elements.useable_run_elements');
        var list2 = _.get(data, 'aggregated.most_recent_proc.data_source');
        list1.sort()
        list2.sort()
        if (!_.isEqual(list1, list2)){
            $(row).addClass('data-source-error');
        }
    }
}


var lims_run_review = function(dt_config) {
    return _lims_review(
        dt_config,
        'run_review',
        'About to review the usability of run elements from <%= n_entities %> samples:'
    )
}


var lims_sample_review = function(dt_config) {
    return _lims_review(
        dt_config,
        'sample_review',
        'About to review the usability of <%= n_entities %> samples:'
    )
}


var _lims_review = function(dt_config, action_type, message_template) {
    return function (e, dt, node, config ) {
        var selected_rows = dt.rows({selected: true}).data();

        // Retrieve the name of all the samples involved using lodash
        var values = _.chain(selected_rows)
                      .map(_.property(dt_config.review_entity_field))
                      .flatten()
                      .filter(function(o) { return o != 'Undetermined'; })
                      .uniq()
                      .sortBy()
                      .value();

        // Grab and store the content of the modal to replace it when it will be closed
        var modalContentClone = $('#reviewModal').clone()
        $('#reviewModal').on('hidden.bs.modal', function (e) {
            $('#reviewModal').replaceWith(modalContentClone);
        });

        $('#modalform').submit(function (event) {
            // Show the spinning arrow
            $('#loadingoverlay').show();

            // Prevent default submit action
            event.preventDefault();
            var usr_input = document.getElementById('usr');
            var pwd_input = document.getElementById('pwd');

            $.ajax({
                url: dt_config.review_url,
                type: 'POST',
                dataType: 'json',
                data: {
                    'username': usr_input.value,
                    'password': pwd_input.value,
                    'review_entities': JSON.stringify(values),
                    'action_type': action_type
                },
                async: true,
                headers: {'Authorization': dt_config.token},
                success: function(json) {
                    // on success write the link to the message div and change it to a success alert
                    var link = $('<a />', {href : json.data.action_info.lims_url, text:json.data.action_info.lims_url});
                    $('#modalmessagediv').empty();
                    $('#modalmessagediv').removeClass('alert-danger')
                    $('#modalmessagediv').addClass('alert-success')
                    $('#modalmessagediv').append(link);
                    $('#modalmessagediv').show();
                    $('#modalsubmit').prop('disabled', true);
                    $('#loadingoverlay').hide();
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    // on error get the error message from the json response and display it in the alert
                    $('#modalmessagediv').empty();
                    $('#modalmessagediv')[0].textContent = jqXHR.responseJSON._error.message;
                    $('#modalmessagediv').addClass('alert-danger')
                    $('#modalmessagediv').show();
                    $('#loadingoverlay').hide();
                }
            });
            return false;
        });
        $('#modaltext')[0].innerHTML = _.template(message_template)({'n_entities': values.length}) + '<br>' + values.join('<br>');
        $('#reviewModal').modal('show')
    }
}

function create_datatable(dt_config){
    //Sets default value using Lodash.js
    _.defaults(dt_config, {'buttons': 'defaults'});
    $(document).ready(function(){
        var table = $('#' + dt_config.name).DataTable(configure_dt(dt_config));
        if (dt_config.buttons){
            new $.fn.dataTable.Buttons(table, {'buttons': configure_buttons(dt_config)});
            table.buttons().container().prependTo(table.table().container());
        }

        // Suport for datatables inserted in each datatable rows
        if (dt_config.child_datatable){
            // Add event listener for opening and closing details
            table.on('click', 'td.details-control', function () {
                var tr = $(this).closest('tr');
                var row = table.row( tr );

                if ( row.child.isShown() ) {
                    // This row is already open - close it
                    row.child.hide();
                    tr.removeClass('shown');
                }
                else {
                    // Open this row
                    format_child_row(row, dt_config.child_datatable);
                    tr.addClass('shown');
                }
            });
        }
    });
}

function format_child_row(row, dt_config, data){
    var data = row.data();
    dt_config.data = _.get(data, dt_config.data_source);
    dt_config.name = _.get(data, dt_config.name_source);
    // Create the html for the table header
    var table_str = '<table id="'+ dt_config.name +'" class="table table-hover table-condensed table-responsive table-striped">'
    table_str += '<thead><tr>'
    dt_config.cols.forEach(function(col){
        table_str += '<th>' + col.title + '</th>'
    });
    table_str += '</tr></thead></table>'
    // attach and show the table
    row.child(table_str).show();
    // Create the datatable
    table = $('#' + dt_config.name).DataTable(configure_dt(dt_config));

    return
}

// Configure the buttons for datatable
var configure_buttons = function(dt_config){

    var buttons_def = {
        'colvis': {extend: 'colvis', text: '<i class="fa fa-filter"></i>', titleAttr: 'Filter Columns'},
        'copy': {extend: 'copy', text: '<i class="fa fa-files-o"></i>', titleAttr: 'Copy', exportOptions: {'columns': ':visible'}},
        'pdf': {extend: 'pdf', text: '<i class="fa fa-file-pdf-o"></i>', titleAttr: 'PDF', orientation: 'landscape', exportOptions: {'columns': ':visible'}},
        'runreview': {extend: 'selected', text: '<i class="fa fa-yelp"></i>', titleAttr: 'Start run review', action: lims_run_review(dt_config)},
        'samplereview': {extend: 'selected', text: '<i class="fa fa-flask"></i>', titleAttr: 'Start sample review', action: lims_sample_review(dt_config)}
    }
    if (dt_config.buttons === 'defaults'){
        dt_config.buttons = ['colvis', 'copy', 'pdf']
    }
    return dt_config.buttons.map(function(n){return buttons_def[n]});
}


// Configure datatable
var configure_dt = function(dt_config) {
    //Sets default value using Lodash.js
    _.defaults(dt_config, {
        'fixed_header': false,
        'paging': true,
        'searching': true,
        'info': true,
        'select': false
    });
    // configure the ajax call or retrieve the ajax callback function
    var ajax_call = {
        'url': dt_config.api_url,
        'dataSrc': 'data',
        'headers': {'Authorization': dt_config.token}
    }
    if (dt_config.data){
        ajax_call = null;

    }else if (dt_config.ajax_call){
        // retrieve the function generating the ajax calls by name and call it with the config
        ajax_call = get_function(dt_config.ajax_call.func_name)(dt_config);
    }
    return {
        'dt_config': dt_config,
        'data': dt_config.data,
        'fixedHeader': dt_config.fixed_header,
        'paging': dt_config.paging,
        'searching': dt_config.searching,
        'info': dt_config.info,
        'processing': true,
        'serverSide': false,
        'autoWidth': false,
        'stateSave': String(dt_config.state_save).toLowerCase() == 'true',
        'lengthMenu': [[10, 25, 50, -1], [10, 25, 50, 'All']],
        'pageLength': 25,
        'select': dt_config.select,
        'ajax': ajax_call,
        'language': {'processing': '<i class="fa fa-refresh fa-spin">'},
        'columns': dt_config.cols.map(
            function(c) {
                return {
                    'data': c.data,
                    'name': c.data,
                    'render': function(data, type, row, meta) {
                        if (type == 'display') {
                            return render_data(data, type, row, meta, c.fmt);
                        } else {
                            return data;
                        }
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
        'createdRow': get_function(dt_config.create_row)
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
                    /* This is a hardcoded workaround, which is expected to be in place until a need for a more generalised
                       solution arises.
                     */
                    if (b instanceof Object){
                        return a + b.samples.length;
                    }
                    else if (b.constructor === Array){
                        return a + b.length;
                    } else if (!isNaN(parseFloat(b)) && isFinite(b)){
                        return a + parseFloat(b);
                    } else if (b === ''){
                        return a;
                    } else {
                        return Number.NaN;
                    }
                }, 0);
        // Update footer
        if (isNaN(sum)){
            $(this.footer()).html('');
        } else {
            $(this.footer()).html(sum);
        }
    });

}
