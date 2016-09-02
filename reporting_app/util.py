from flask import request
from auth import encode_string
from config import col_mappings


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
        'token': encode_string(request.cookies.get('remember_token'))
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
