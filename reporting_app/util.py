import auth
from config import col_mappings

invalid_attr_chars = str.maketrans({k: '_' for k in (' ', ',')})


def _format_order(col_name, cols):
    direction = 'desc' if col_name.startswith('-') else 'asc'
    return [[c['data'] for c in cols].index(col_name.lstrip('-')), direction]


def datatable_cfg(title, cols, api_url=None, ajax_call=None, default_sort_col=None, **kwargs):
    if not api_url and not ajax_call:
        raise ValueError('Either api_url or ajax_call must be provided')
    if default_sort_col is None:
        default_sort_col = [0, 'desc']
    else:
        default_sort_col = _format_order(default_sort_col, col_mappings[cols])

    d = {
        'title': title,
        'name': snake_case(title),
        'cols': col_mappings[cols],
        'api_url': api_url,
        'ajax_call': ajax_call,
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
    return 'Token ' + auth.User.get_login_token()


def capitalise(word):
    return word[0].upper() + word[1:]


def snake_case(text):
    return text.translate(invalid_attr_chars).lower()
