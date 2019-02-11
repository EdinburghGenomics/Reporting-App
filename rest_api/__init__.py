import eve
import pymongo

import auth
import flask_cors
from eve.auth import requires_auth
from os.path import join, abspath, dirname
from config import rest_config as cfg
from rest_api import actions
from rest_api.limsdb import lims_extract
from rest_api.aggregation import database_hooks

app = eve.Eve(settings=join(dirname(abspath(__file__)), 'settings.py'), auth=auth.DualAuth)
app.secret_key = cfg['key'].encode()
flask_cors.CORS(app, supports_credentials=True, allow_headers=('Authorization',))

app.on_inserted += database_hooks.post_insert_hook
app.on_updated += database_hooks.post_update_hook
app.on_pre_POST_actions += actions.start_action
app.on_post_POST_actions += actions.add_to_action


def _create_url_with(base, route):
    if app.config.get('URL_PREFIX') and app.config.get('API_VERSION'):
        return '/%s/%s/%s/%s' % (app.config['URL_PREFIX'], app.config['API_VERSION'], base, route)
    return '/' + base + '/' + route  # Apache adds url prefix instead


def _lims_endpoint(route):
    return _create_url_with('lims', route)


# Keep this for now for backward compatibility
@app.route(_lims_endpoint('status/<status_type>'))
@requires_auth('home')
def lims_status_info(status_type):
    return lims_extract(
        status_type,
        app
    )


# Keep this for now for backward compatibility
@app.route(_lims_endpoint('samples'))
@requires_auth('home')
def lims_sample_info():
    return lims_extract(
        'sample_info',
        app
    )


@app.route(_lims_endpoint('<endpoint>'))
@requires_auth('home')
def lims_info(endpoint):
    return lims_extract(
        endpoint,
        app
    )
