import { build_series } from '../../reporting_app/src/plate_view.js';

test('build_series', () => {
    window.container_data = [{
        'id': 'a_library',
        'location': 'A:1',
        'name': 'a_sample',
        'udf': {'a_udf': 13.37},
        'reporting_app': {'a_rest_api_metric': 13.38}
    }];
    window.heatmap_y_category = 'ABCDEFGH';
    window.metrics = {
        'a_metric': {'data': ['reporting_app', 'a_rest_api_metric']},
        'another_metric': {'data': ['udf', 'a_udf']}
    };

    expect(build_series('a_metric')).toEqual(
        {
            name: 'a_library',
            dataLabels: {enabled: false},
            data: [
                {'y': 0, 'x': 0, 'value': 13.38, 'name': 'a_sample'}
            ]
        }
    );
    expect(build_series('another_metric')['data'][0]['value']).toBe(13.37);
});

