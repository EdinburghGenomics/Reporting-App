{% macro dt_init(name, cols, api_url) %}

$(document).ready(
    function() {
        // the table name needs to be hard-coded, otherwise all datatable scripts on the page will initialise
        // the last table, for some reason.
        var cols = {{ cols|list|safe }};
        var api_url = '{{ api_url|safe }}';
        $('#{{name}}').DataTable(
            {
                'searching': false,
                'processing': true,
                'serverSide': true,
                'ajax': function(data, callback, settings) {

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
                            'dataType': 'jsonp',
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
                            'defaultContent': ''
                        };
                    }
                ),
                'order': [[0, 'asc']]
            }
        );
    }
);
{% endmacro %}
