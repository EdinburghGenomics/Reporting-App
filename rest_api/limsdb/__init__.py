from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from genologics_sql.tables import Base
from flask import jsonify

from config import rest_config as cfg
from rest_api.limsdb.queries import factories

_session = None


def get_session(echo=False):
    """
    Generate a SQLAlchemy session based on the CONF
    :returns: the SQLAlchemy session
    """
    global _session
    if _session is None:
        if 'lims_database' in cfg:
            uri = "postgresql://{username}:{password}@{url}/{db}".format(**cfg.get('lims_database'))
            engine = create_engine(uri, echo=echo, isolation_level="AUTOCOMMIT")
        else:
            engine = create_engine('sqlite:///:memory:')
        Base.metadata.bind = engine
        Base.metadata.create_all(engine)
        DBSession = sessionmaker(bind=engine)
        _session = DBSession()
    return _session


function_mapping = {
    'project_status': factories.sample_status_per_project,
    'plate_status': factories.sample_status_per_plate,
    'sample_status': factories.sample_status,
    'run_status': factories.run_status,
    'sample_info': factories.sample_info,
    'project_info': factories.project_info
}


def lims_extract(endpoint, app):
    data = function_mapping[endpoint](get_session())
    ret_dict = {app.config['META']: {'total': len(data)}, app.config['ITEMS']: data}
    return jsonify(ret_dict)
