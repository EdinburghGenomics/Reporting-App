import auth
import flask_login
from config import col_mappings


def _format_order(col_name, cols):
    direction = 'desc' if col_name.startswith('-') else 'asc'
    return [[c['data'] for c in cols].index(col_name.lstrip('-')), direction]


def construct_url(endpoint, **query_args):
    url = flask_login.current_user.comm.api_url(endpoint)
    if query_args:
        url += '?' + '&'.join(['%s=%s' % (k, v) for k, v in query_args.items()])
    return url.replace('\'', '"')


def datatable_cfg(title, cols, api_url=None, ajax_call=None, default_sort_col=None, minimal=False, review=None, **kwargs):
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
    return text.lower().replace(' ', '_')
