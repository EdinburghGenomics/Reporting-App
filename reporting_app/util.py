import datetime
import flask_login
from json import dumps
import auth
from config import col_mappings, chart_metrics_mappings

invalid_attr_chars = str.maketrans({k: '_' for k in (' ', ',')})


def _format_order(col_name, cols):
    direction = 'desc' if col_name.startswith('-') else 'asc'
    return [
        [c['name'] for c in cols].index(col_name.lstrip('-')),
        direction
    ]


def construct_url(endpoint, **query_args):
    url = flask_login.current_user.comm.api_url(endpoint)
    if query_args:
        _query_args = []
        for k in sorted(query_args):
            q = query_args[k]
            if isinstance(q, dict):
                q = dumps(q, sort_keys=True)

            _query_args.append('%s=%s' % (k, q))

        url += '?' + '&'.join(_query_args)
    return url.replace(' ', '')


def resolve_cols(col):
    """Resolve the columns that will be used """
    if isinstance(col, str):
        return col_mappings.get(col) or chart_metrics_mappings.get(col)
    elif isinstance(col, list):
        res = list()
        for c in col:
            res.extend(resolve_cols(c))
        return res


def datatable_cfg(title, cols, api_url=None, ajax_call=None, default_sort_col=None, minimal=False,
                  review=None, **kwargs):
    if not api_url and not ajax_call and not kwargs.get('data_source'):
        raise ValueError('Either api_url, ajax_call or data_source must be provided')
    if default_sort_col is None:
        default_sort_col = [0, 'desc']
    else:
        default_sort_col = _format_order(default_sort_col, col_mappings[cols])

    d = {
        'title': title,
        'name': snake_case(title),
        'cols': resolve_cols(cols),
        'api_url': api_url,
        'ajax_call': ajax_call,
        'default_sort_col': default_sort_col,
        'token': get_token()
    }
    d.update(kwargs)

    if minimal:
        d.update({'paging': False, 'searching': False, 'info': False})

    if review:
        d.update(
            {
                'select': {'style': 'os', 'blurable': True},
                'review_url': construct_url('actions'),
                'review_entity_field': review['entity_field'],
                'buttons': ['colvis', 'copy', 'pdf', review['button_name']]
            }
        )

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


def now():
    return datetime.datetime.now()
