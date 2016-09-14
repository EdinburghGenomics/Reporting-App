from flask import request
from auth import encode_string
from config import col_mappings
import datetime, time


def _format_order(col_name, cols):
    direction = 'desc' if col_name.startswith('-') else 'asc'
    return [[c['data'] for c in cols].index(col_name.lstrip('-')), direction]


def datatable_cfg(title, cols, api_url, default_sort_col=None, **kwargs):
    if default_sort_col is None:
        default_sort_col = [0, 'desc']
    else:
        default_sort_col = _format_order(default_sort_col, col_mappings[cols])

    d = {
        'title': title,
        'name': snake_case(title),
        'cols': col_mappings[cols],
        'api_url': api_url,
        'default_sort_col': default_sort_col,
        'token': get_token()
    }
    d.update(kwargs)
    return d


def tab_set_cfg(title, tables):
    return {
        'title': title,
        'name': snake_case(title),
        'tables': tables
    }

def get_token():
    return 'Token ' + encode_string(request.cookies.get('remember_token'))


def capitalise(word):
    return word[0].upper() + word[1:]


def snake_case(text):
    return text.lower().replace(' ', '_')




def chart_variables(endpoint, data):

    clean_yield_gb = [d['clean_yield_in_gb'] for d in data]
    clean_yield_q30_gb = None

    if endpoint == 'aggregate/samples':
        clean_yield_q30_gb = [d['clean_yield_q30'] for d in data]
    elif endpoint == 'aggregate/all_runs':
        clean_yield_q30_gb = [d['clean_yield_q30_in_gb'] for d in data]

    histogram_variables = []
    histogram_variables.append(['clean yield q30 (gb)', 'clean yield (gb)'])
    for r in range(len(clean_yield_gb)):
        hist_variable = [clean_yield_q30_gb[r], clean_yield_gb[r]]
        histogram_variables.append(hist_variable)

    return histogram_variables



def run_name_to_date(run_id):
    run_date = int(run_id.split('_')[0])
    year = int(''.join(list(str(run_date))[0:2])) + 2000
    month = int(''.join(list(str(run_date))[2:4]))
    day = int(''.join(list(str(run_date))[4:6]))
    d = datetime.datetime(year, month, day)
    date = int(time.mktime(d.timetuple())) * 1000
    return date


def yield_by_date(data):
    date_yield = []
    for d in data:
        run_id = d.get('_id')
        date = run_name_to_date(run_id)
        run_yield = [d.get('yield_in_gb')]
        date_yield.append([date, run_yield])
    return date_yield


def sample_sequencing_metrics(data):
    date_samples_first_sequenced = []
    date_samples_repeat_sequened = []
    date_samples_sequenced_total = []
    samples2date = {}
    samples_per_date = []
    for d in data:
        run_ids = ((sorted(d.get('all_run_ids'))))
        if len(run_ids) == 1:
            date = run_name_to_date(run_ids[0])
            date_samples_first_sequenced.append(date)
            date_samples_sequenced_total.append(date)
            samples2date[date] = [0, 0, 0]
        elif len(run_ids) > 1:
            date = run_name_to_date(run_ids[0])
            date_samples_first_sequenced.append(date)
            date_samples_sequenced_total.append(date)
            samples2date[date] = [0, 0, 0]


            run_ids = run_ids[1:]
            for run in run_ids:
                date = run_name_to_date(run)
                date_samples_repeat_sequened.append(date)
                date_samples_sequenced_total.append(date)
                samples2date[date] = [0, 0, 0]

    for date in date_samples_first_sequenced:
        samples2date[date][0] += 1
    for date in date_samples_repeat_sequened:
        samples2date[date][1] += 1
    for date in date_samples_sequenced_total:
        samples2date[date][2] += 1

    return_samples2date = []

    for date in samples2date:
        format_date = [date, samples2date[date]]
        return_samples2date.append(format_date)
    return_samples2date.sort(key=lambda x: x[0])
    return return_samples2date








