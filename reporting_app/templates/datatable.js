{% macro dt_init(name, cols, api_url, default_sort_col, paging) %}

$(document).ready(
    function() {
        var cols = {{ cols|list|safe }};
        var api_url = '{{ api_url|safe }}';
        var paging = {{ paging|safe }};
        var default_sort_col = {{ default_sort_col|safe }};

        var table = $('#{{name}}').DataTable(
            {
                'paging': paging,
                'searching': true,
                'processing': true,
                'serverSide': false,
                'autoWidth': false,
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

        new $.fn.dataTable.Buttons(table, {'buttons': [{'extend': 'colvis', 'text': 'Filter columns'}]});
        table.buttons().container().prependTo(table.table().container());
    }
);

{% endmacro %}
