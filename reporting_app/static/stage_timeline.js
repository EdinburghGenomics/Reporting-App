
function _to_moment(str_date) {
    return moment(str_date, 'DD_MM_YYYY_HH:mm:SS');
}


function _reformat(date) {
    return _to_moment(date).format('YYYY-MM-DD HH:mm:ss');
}


function build_tooltip(stage) {
    var t = '<div><b>' + stage.stage_name + '</b><br/>Started: ' + _reformat(stage.date_started) + '<br/>';

    var stage_end;
    if (stage.date_finished) {
        stage_end = _to_moment(stage.date_finished);
        t += 'Finished: ' + _reformat(stage.date_finished) + '<br/>';
        t += 'Exit status: ' + stage.exit_status + '<br/>';
    } else {
        stage_end = moment();
    }
    t += 'Time elapsed: ' + moment.duration(stage_end.diff(_to_moment(stage.date_started))).humanize();
    t += '<br/></div>';
    return t;
}


function stage_timeline(div_id, proc) {
    var stages;

    if (proc.stages === undefined) {
        stages = []
    } else {
        stages = proc.stages.map(
            function(s) {
                var o = {
                    'start': _to_moment(s.date_started),
                    'style': 'display: block; overflow: visible',
                    'content': s.stage_name,
                    'title': build_tooltip(s)
                };

                if (s.date_finished) {
                    o['end'] = _to_moment(s.date_finished);
                    if (s.exit_status == 0) {
                        o['style'] += '; background-color: #c2e0c6; border-color: #0e8a16';  // green
                    } else {
                        o['style'] += '; background-color: #f7c6c7; border-color: #b60205';  // red
                    }
                } else {
                    o['end'] = moment();
                }
                return o;
            }
        );
    }

    var items = new vis.DataSet(stages);
    var startDate = _to_moment(proc._created);
    var options = {'tooltip': {'followMouse': true, 'overflowMethod': 'cap'}};

    var timeline = new vis.Timeline(document.getElementById(div_id), items, options);
}
