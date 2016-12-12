{% macro dt_init(dt_config) %}

$(document).ready(
    function() {
        var cols = {{ dt_config.cols|list|safe }};
        var api_url = '{{ dt_config.api_url|safe }}';
        var paging = {{'true' if dt_config.paging|default(true) else 'false' }};
        var searching = {{'true' if dt_config.searching|default(true) else 'false' }};
        var info = {{'true' if dt_config.info|default(true) else 'false' }};
        var default_sort_col = {{ dt_config.default_sort_col|safe }};
        var fixed_header = {{'true' if dt_config.fixed_header|default(false) else 'false' }};
        var table = $('#{{dt_config.name}}').DataTable(
            {
                'fixedHeader': fixed_header,
                'paging': paging,
                'searching': searching,
                'info': info,
                'processing': true,
                'serverSide': false,
                'autoWidth': false,
                //'stateSave': true,
                'lengthMenu': [[10, 25, 50, -1], [10, 25, 50, "All"]],
                'pageLength': 25,
                'ajax': {
                    'url': api_url,
                    'dataSrc': 'data',
                    'headers': {'Authorization': '{{ dt_config.token }}'}
                },
                'language': {'processing': '<i class="fa fa-refresh fa-spin">'},
                'columns': cols.map(
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
                'order': [default_sort_col],
                "footerCallback": {{ dt_config.table_foot if dt_config.table_foot else 'null'}}
            }
        );

        new $.fn.dataTable.Buttons(table, {'buttons': [
               {'extend': 'colvis', 'text': '<i class="fa fa-filter"></i>',     'titleAttr': 'Filter Columns'},
               {'extend': 'copy',   'text': '<i class="fa fa-files-o"></i>',    'titleAttr': 'Copy', 'exportOptions': {'columns': ':visible'} },
               {'extend': 'pdf',    'text': '<i class="fa fa-file-pdf-o"></i>', 'titleAttr': 'PDF', 'orientation': 'landscape', 'exportOptions': {'columns': ':visible'}}
        ]});
        table.buttons().container().prependTo(table.table().container());
    }
);

function sum_row_per_column( row, data, start, end, display ) {
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


{% endmacro %}



