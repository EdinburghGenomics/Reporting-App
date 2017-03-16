//helper function to retrieve a function by name
function get_function(fn_name){
    var fn = window[fn_name];
    if(typeof fn === 'function') {
        return fn;
    }else{
        return null;
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
function configure_buttons(button_config){
    buttons_def = {
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
function configure_dt(dt_config) {
    //Sets default value using Lodash.js
    _.defaults(dt_config, {
        'fixed_header': false,
        'paging': true,
        'searching': true,
        'info': true,
    });
    return {
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
        'ajax': {
            'url': dt_config.api_url,
            'dataSrc': 'data',
            'headers': {'Authorization': dt_config.token}
        },
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
        "footerCallback": get_function(dt_config.table_foot)
    }

}

// Helper function that sums the value of a column
function sum_row_per_column( row, data, start, end, display ) {
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



