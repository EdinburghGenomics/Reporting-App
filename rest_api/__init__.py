import json
import eve
import enum
from eve_sqlalchemy import SQL
from eve_sqlalchemy.decorators import registerSchema
from eve_sqlalchemy.validation import ValidatorSQL
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Boolean
from sqlalchemy import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy_utils import aggregated
from config import rest_config as cfg


class EveColumns:
    reportable_fields = None

    id = Column(String(24), unique=True)  # , default=random_string(24))
    _created = Column(DateTime, default=func.now())
    _updated = Column(DateTime, default=func.now(), onupdate=func.now())
    _etag = Column(String(40), unique=True)  # , default=random_string(40), onupdate=random_string(40))

    @property
    def item_title(self):
        return self.__class__.__name__.lower()

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join(['%s=%s' % (f, self.__getattribute__(f)) for f in self.reportable_fields])
        )


Base = declarative_base(cls=EveColumns)
# TODO: see if we can filter on useable == None


class RunElement(Base):
    __tablename__ = 'run_elements'
    reportable_fields = ('run_id', 'lane', 'barcode', 'sample_id')
    item_title = 'run_element'

    run_id = Column(String, ForeignKey('sequencing_runs.run_id'), ForeignKey('lanes.run_id'), primary_key=True)
    lane_number = Column(Integer, primary_key=True)
    barcode = Column(String, primary_key=True)

    sample_id = Column(String, ForeignKey('samples.sample_id'))

    sequencing_lane = relationship('SequencingLane', back_populates='run_elements')
    sample = relationship('Sample', back_populates='run_elements')
    run = relationship('SequencingRun', back_populates='run_elements')


class UnexpectedBarcode(Base):
    __tablename__ = 'unexpected_barcodes'
    reportable_fields = ('run_id', 'lane', 'barcode')
    item_title = 'unexpected_barcode'

    run_id = Column(String, ForeignKey('lanes.run_id'), primary_key=True)
    lane_number = Column(Integer, primary_key=True)
    barcode = Column(String, primary_key=True)

    sequencing_lane = relationship('SequencingLane', back_populates='unexpected_barcodes')


class Sample(Base):
    __tablename__ = 'samples'
    reportable_fields = ('sample_id', 'run_elements')

    sample_id = Column(String, unique=True, primary_key=True)
    project_id = Column(String, ForeignKey('projects.project_id'))

    project = relationship('Project', back_populates='samples')
    run_elements = relationship('RunElement', back_populates='sample')


class SequencingRun(Base):
    __tablename__ = 'sequencing_runs'
    reportable_fields = ('run_id', 'number_of_lanes')
    item_title = 'sequencing_run'

    run_id = Column(String, unique=True, primary_key=True)

    lanes = relationship('SequencingLane', back_populates='run')
    run_elements = relationship('RunElement', back_populates='run', viewonly=True)


class SequencingLane(Base):
    __tablename__ = 'lanes'
    item_title = 'lane'

    run_id = Column(String, ForeignKey('sequencing_runs.run_id'), primary_key=True)
    run = relationship('SequencingRun', back_populates='lanes')
    lane_number = Column(Integer, primary_key=True)

    run_elements = relationship('RunElement', back_populates='sequencing_lane', viewonly=True)
    unexpected_barcodes = relationship('UnexpectedBarcode', back_populates='sequencing_lane')


class Project(Base):
    __tablename__ = 'projects'
    reportable_fields = ('project_id',)

    project_id = Column(String, unique=True, primary_key=True)
    samples = relationship('Sample', back_populates='project')


class PipelineRun(Base):
    __tablename__ = 'pipeline_runs'
    reportable_fields = ('dataset_type', 'dataset_name', 'start_date')
    item_title = 'pipeline_run'

    dataset_name = Column(String, ForeignKey('sequencing_runs.run_id'), ForeignKey('samples.sample_id'), primary_key=True)
    start_date = Column(DateTime, primary_key=True)




# class PipelineStage(Base):
#     __tablename__ = 'pipeline_stages'
#     reportable_fields = ('dataset_type', 'dataset_name', 'stage_name')
#     item_title = 'pipeline_stage'


tables = (RunElement, UnexpectedBarcode, Sample, SequencingRun, Project, PipelineRun)#, PipelineStage)
for table in tables:
    r = registerSchema(table.__tablename__)
    r(table)


sqlite_db = '/Users/mwham/workspace/sqlite/test'

settings = {
    'DOMAIN': {},

    'ID_FIELD': 'id',
    'VALIDATE_FILTERS': True,
    'ITEMS': 'data',

    'XML': False,

    'PAGINATION': True,
    'PAGINATION_LIMIT': 100000,

    'X_DOMAINS': cfg['x_domains'],

    'URL_PREFIX': 'api',
    'API_VERSION': '0.1',

    'RESOURCE_METHODS': ['GET', 'POST', 'DELETE'],
    'ITEM_METHODS': ['GET', 'PUT', 'PATCH', 'DELETE'],

    # 'CACHE_CONTROL': 'max-age=20',
    # 'CACHE_EXPIRES': 20,

    'DATE_FORMAT': '%d_%m_%Y_%H:%M:%S',

    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///' + sqlite_db,
    # 'SQLALCHEMY_BINDS',
    # 'SQLALCHEMY_NATIVE_UNICODE',
    # 'SQLALCHEMY_ECHO',
    # 'SQLALCHEMY_RECORD_QUERIES',
    # 'SQLALCHEMY_POOL_SIZE',
    # 'SQLALCHEMY_POOL_TIMEOUT',
    # 'SQLALCHEMY_POOL_RECYCLE',
    # 'SQLALCHEMY_MAX_OVERFLOW',
    # 'SQLALCHEMY_COMMIT_ON_TEARDOWN'
}

for table in tables:
    n = table.__tablename__
    s = table._eve_schema[n]
    settings['DOMAIN'][n] = s
    settings['DOMAIN'][n].update(
        {'item_title': table.item_title, 'item_lookup_field': 'id'}
    )
    print(n)
    print(s)
    # for f in table.aggregated_fields:
    #     settings['DOMAIN'][n]['schema'].update(
    #         {f: {'unique': False, 'type': 'string', 'nullable': True, 'required': False}}
    #     )


def format_json(resource, request, response):
    response.data = json.dumps(json.loads(response.data.decode('utf-8')), indent=4).encode()


if __name__ == '__main__':
    app = eve.Eve(settings=settings, data=SQL, validator=ValidatorSQL)

    from sqlalchemy import create_engine

    db = app.data.driver
    db.engine.echo = 'debug'
    Base.metadata.bind = db.engine
    db.Model = Base
    db.create_all()

    app.on_post_GET += format_json
    app.run(port=4999, debug=True, use_reloader=False)
'''
query = db.session.query(Sample).filter_by(sample_id='sample_1').all()
print(query)

s = query[0]
print(s.run_elements)
'''
