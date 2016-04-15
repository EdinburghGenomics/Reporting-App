import requests
from flask import json
from config import reporting_app_config as cfg, col_mappings


def rest_query(resource, **query_args):
    if not query_args:
        return cfg['rest_api'] + '/' + resource

    query = '?'
    query += '&'.join(['%s=%s' % (k, v) for k, v in query_args.items()]).replace(' ', '').replace('\'', '"')
    return cfg['rest_api'] + '/' + resource + query


def query_api(resource, data_only=True, **query_args):
    url = rest_query(resource, **query_args)
    j = json.loads(requests.get(url).content.decode('utf-8'))
    if data_only:
        j = j['data']
    return j


def _format_order(col_name, cols):
    direction = 'desc' if col_name.startswith('-') else 'asc'
    return [[c['data'] for c in cols].index(col_name.lstrip('-')), direction]


def datatable_cfg(title, name, cols, api_url, paging=True, default_sort_col=None):
    if default_sort_col is None:
        default_sort_col = [0, 'desc']
    else:
        default_sort_col = _format_order(default_sort_col, col_mappings[cols])
    return {
        'title': title,
        'name': name,
        'cols': col_mappings[cols],
        'api_url': api_url,
        'default_sort_col': default_sort_col,
        'paging': paging
    }


def tab_set_cfg(title, name, tables):
    return {
        'title': title,
        'name': name,
        'tables': tables
    }
