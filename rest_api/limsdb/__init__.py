from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from genologics_sql.tables import Base
from flask import jsonify, request
from eve.utils import parse_request
from eve.methods.get import _pagination_links, _meta_links
from config import rest_config as cfg
from rest_api.limsdb.queries import sample_status, run_status

_session = None


def get_engine(echo=False):
    """
    Generate a SQLAlchemy engine for PostGres with the CONF currently used
    :returns: the SQLAlchemy engine
    """
    uri = "postgresql://{username}:{password}@{url}/{db}".format(**cfg.get('lims_database'))
    return create_engine(uri, echo=echo, isolation_level="AUTOCOMMIT")


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
    'project_status': sample_status.sample_status_per_project,
    'plate_status': sample_status.sample_status_per_plate,
    'sample_status': sample_status.sample_status,
    'run_status': run_status.run_status
}


def lims_extract(endpoint, app):
    data = function_mapping[endpoint](get_session())
    ret_dict = {app.config['META']: {'total': len(data)}, app.config['ITEMS']: data}
    return jsonify(ret_dict)
