import requests
import auth
from flask_login import current_user
from config import reporting_app_config as cfg, col_mappings


def rest_query(resource, **query_args):
    if not query_args:
        return cfg['rest_api'] + '/' + resource

    query = '?'
    query += '&'.join(['%s=%s' % (k, v) for k, v in query_args.items()]).replace(' ', '').replace('\'', '"')
    return cfg['rest_api'] + '/' + resource + query


def query_api(resource, data_only=True, **query_args):
    url = rest_query(resource, **query_args)
    r = requests.get(url, headers={'Authorization': 'Token ' + auth.encode_string(current_user.api_token)})
    j = r.json()
    if data_only:
        j = j['data']
    return j


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
        'token': current_user.api_token
    }
    d.update(kwargs)
    return d


def tab_set_cfg(title, tables):
    return {
        'title': title,
        'name': snake_case(title),
        'tables': tables
    }


def capitalise(word):
    return word[0].upper() + word[1:]


def snake_case(text):
    return text.lower().replace(' ', '_')
