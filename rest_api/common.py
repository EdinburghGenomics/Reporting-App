import json
import datetime
from flask import request, current_app as app


def retrieve_args():
    """Retrieve args from a request sent to flask and convert the dates to datetime"""
    d = {}
    for key in request.args:
        if len(request.args.getlist(key)) == 1:
            d[key] = request.args.get(key)
        else:
            d[key] = request.args.getlist(key)
        if key in ['match', 'where']:
            d[key] = json.loads(d[key])
    return convert_date(d)


def convert_date(source):
    """Recursively iterates a JSON dictionary, turning date strings into datetime values."""
    def try_cast(v):
        try:
            return datetime.datetime.strptime(v, app.config['DATE_FORMAT'])
        except ValueError:
            return v
    if isinstance(source, list):
        for i, v in enumerate(source):
            source[i] = convert_date(v)
    elif isinstance(source, dict):
        for k, v in source.items():
            source[k] = convert_date(v)
    elif isinstance(source, str):
        return try_cast(source)

    return source
