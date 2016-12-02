from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from genologics_sql.tables import Base
from flask import jsonify, request
from eve.utils import parse_request
from eve.methods.get import _pagination_links, _meta_links
from config import rest_config as cfg
from rest_api.limsdb.queries.project_status import sample_status_per_project, sample_info

_session = None


def get_engine(echo=False):
    """
    Generate a SQLAlchemy engine for PostGres with the CONF currently used
    :returns: the SQLAlchemy engine
    """
    uri = "postgresql://{username}:{password}@{url}/{db}".format(**cfg.get('lims_database'))
    return create_engine(uri, echo=echo)


def get_session(echo=False):
    """
    Generate a SQLAlchemy session based on the CONF
    :returns: the SQLAlchemy session
    """
    global _session
    if _session is None:
        engine = get_engine(echo=echo)
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        _session = DBSession()
    return _session


function_mapping = {
    'project_status': sample_status_per_project
}


def lims_extract(endpoint, app):
    data = function_mapping[endpoint](get_session())
    total_items = len(data)
    ret_dict = {}
    page_number = int(request.args.get(app.config['QUERY_PAGE'], '0'))
    page_size = int(request.args.get(app.config['QUERY_MAX_RESULTS'], '0'))
    if page_number and page_size:
        data = data[page_size * (page_number - 1): page_size * page_number]
        req = parse_request(endpoint)
        ret_dict[app.config['META']] = _meta_links(req, total_items),
        ret_dict[app.config['LINKS']] = _pagination_links(endpoint, req, total_items)
    else:
        ret_dict[app.config['META']] = {'total': total_items}
    ret_dict[app.config['ITEMS']] = data
    j = jsonify(ret_dict)
    return j
