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
                'searching': false,
                'processing': true,
                'serverSide': true,
                'autoWidth': false,
                'ajax': function(data, callback, settings) {

                    // workaround: if paging is false, data.length is set to -1 and passed to max_results
                    if (paging == false) {
                        data.length = 50;
                    }

                    // convert [{'column': 0, 'dir': 'asc'}, {'column': 1, 'dir': 'desc'}]
                    // to [cols[0], '-' + cols[1]]
                    var sortCols = new Array();
                    data.order.forEach(
                        function(s) {
                            if (s.dir == 'desc') {
                                sortCols.push('-' + cols[s.column].name);
                            } else {
                                sortCols.push(cols[s.column].name);
                            }
                        }
                    );

                    $.ajax(
                        {
                            'url': api_url,
                            'data': {
                                'max_results': data.length,
                                'page': (data.start/data.length) + 1,
                                // convert [cols[0], '-' + cols[1]] to '%s,-%s' % (cols[0], cols[1])
                                'sort': sortCols.toString()
                            },
                            'success': function(json) {
                                var o = {
                                    recordsTotal: json._meta.total,
                                    recordsFiltered: json._meta.total,
                                    data: json.data
                                };
                                callback(o);
                            }
                        }
                    );

                },
                'columns': cols.map(
                    function(c) {
                        return {
                            'data': c.name,
                            'render': function(data, type, row, meta) {
                                return render_data(data, c.fmt)
                            },
                            'orderable': !c.orderable || String(c.orderable).toLowerCase() == 'true',
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
