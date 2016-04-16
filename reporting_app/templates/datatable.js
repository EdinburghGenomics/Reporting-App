{% macro dt_init(dt_config) %}

$(document).ready(
    function() {
        var cols = {{ dt_config.cols|list|safe }};
        var api_url = '{{ dt_config.api_url|safe }}';
        var paging = {{'true' if dt_config.paging|default(true) else 'false' }};
        var searching = {{'true' if dt_config.searching|default(true) else 'false' }};
        var info = {{'true' if dt_config.info|default(true) else 'false' }};
        var default_sort_col = {{ dt_config.default_sort_col|safe }};

        var table = $('#{{dt_config.name}}').DataTable(
            {
                'paging': paging,
                'searching': searching,
                'info': info,
                'processing': true,
                'serverSide': false,
                'autoWidth': false,
                'stateSave': true,
                'ajax': {
                    'url': api_url,
                    'dataSrc': 'data'
                },
                'columns': cols.map(
                    function(c) {
                        return {
                            'data': c.data,
                            'render': function(data, type, row, meta) {
                                return render_data(data, c.fmt)
                            },
                            'orderable': !c.orderable || String(c.orderable).toLowerCase() == 'true',
                            'visible': !c.visible || String(c.visible).toLowerCase() == 'true',
                            'defaultContent': ''
                        };
                    }
                ),
                'order': [default_sort_col]
            }
        );

        new $.fn.dataTable.Buttons(table, {'buttons': [
               {'extend': 'colvis', 'text': '<i class="fa fa-filter"></i>',     'titleAttr': 'Filter Columns'},
               {'extend': 'copy',   'text': '<i class="fa fa-files-o"></i>',    'titleAttr': 'Copy'},
               {'extend': 'pdf',    'text': '<i class="fa fa-file-pdf-o"></i>', 'titleAttr': 'PDF'}
        ]});
        table.buttons().container().prependTo(table.table().container());
    }
);

{% endmacro %}
