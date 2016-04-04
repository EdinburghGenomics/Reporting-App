import enum
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Enum, Boolean, cast, FetchedValue
from sqlalchemy import func
from sqlalchemy.sql import select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils import aggregated

# TODO: see if we can filter on useable == None


def _relationship(target, back_populates, **kwargs):
    return relationship(target, back_populates=back_populates, viewonly=True, **kwargs)


dataset_types = ('sequencing_run', 'sample')
review_statuses = ('passed', 'failed', 'not_reviewed')
genders = ('female', 'male', 'unknown')


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


class RunElement(Base):
    __tablename__ = 'run_elements'
    reportable_fields = ('run_id', 'lane', 'barcode', 'sample_id')
    item_title = 'run_element'

    run_id = Column(String, ForeignKey('sequencing_runs.run_id'), ForeignKey('lanes.run_id'), primary_key=True)
    lane_number = Column(Integer, primary_key=True)
    barcode = Column(String, primary_key=True)

    project_id = Column(String, ForeignKey('projects.project_id'))
    sample_id = Column(String, ForeignKey('samples.sample_id'))
    library_id = Column(String)

    passing_filter_reads = Column(Integer)
    pc_reads_in_lane = Column(Float)
    total_reads = Column(Integer)
    bases_r1 = Column(Integer)
    q30_bases_r1 = Column(Integer)
    bases_r2 = Column(Integer)
    q30_bases_r2 = Column(Integer)
    adaptor_bases_removed_r1 = Column(Integer)
    adaptor_bases_removed_r2 = Column(Integer)
    clean_reads = Column(Integer)
    clean_bases_r1 = Column(Integer)
    clean_q30_bases_r1 = Column(Integer)
    clean_bases_r2 = Column(Integer)
    clean_q30_bases_r2 = Column(Integer)
    fastqc_report_r1 = Column(String)
    fastqc_report_r2 = Column(String)
    reviewed = Column(Enum(*review_statuses), default='not_reviewed')
    useable = Column(Boolean, nullable=True)

    sequencing_lane = _relationship('SequencingLane', 'run_elements')
    sample = _relationship('Sample', 'run_elements')
    run = _relationship('SequencingRun', 'run_elements')

    # @hybrid_property
    # def pc_pass_filter(self):
    #     return round(self.passing_filter_reads / self.total_reads * 100, 2)
    #
    # @pc_pass_filter.expression
    # def pc_pass_filter(cls):
    #     return RunElement.passing_filter_reads


class UnexpectedBarcode(Base):
    __tablename__ = 'unexpected_barcodes'
    reportable_fields = ('run_id', 'lane', 'barcode')
    item_title = 'unexpected_barcode'

    run_id = Column(String, ForeignKey('lanes.run_id'), primary_key=True)
    lane_number = Column(Integer, primary_key=True)
    barcode = Column(String, primary_key=True)

    passing_filter_reads = Column(Integer)
    pc_reads_in_lane = Column(Float)

    sequencing_lane = _relationship('SequencingLane', 'unexpected_barcodes')


class Sample(Base):
    __tablename__ = 'samples'
    reportable_fields = ('sample_id', 'run_elements')

    sample_id = Column(String, unique=True, primary_key=True)
    project_id = Column(String, ForeignKey('projects.project_id'))

    user_sample_id = Column(String)
    library_id = Column(String)
    bam_file_reads = Column(Integer)
    mapped_reads = Column(Integer)
    properly_mapped_reads = Column(Integer)
    duplicate_reads = Column(Integer)
    median_coverage = Column(Float)
    pc_callable = Column(Float)
    freemix = Column(Float)
    called_gender = Column(Enum(*genders))
    provided_gender = Column(Enum(*genders))
    reviewed = Column(Enum(*review_statuses), default='not_reviewed')
    useable = Column(Boolean, nullable=True)
    delivered = Column(Boolean, default=False)
    input_fastqs_deleted = Column(Boolean, default=False)

    project = _relationship('Project', 'samples')
    run_elements = _relationship('RunElement', 'sample')
    pipeline_runs = _relationship('PipelineRun', 'sample')

    @aggregated('run_elements', Column(Integer))
    def total_bases_r1(self):
        return func.sum(RunElement.bases_r1)


class SequencingRun(Base):
    __tablename__ = 'sequencing_runs'
    reportable_fields = ('run_id', 'number_of_lanes')
    item_title = 'sequencing_run'

    run_id = Column(String, unique=True, primary_key=True)

    pipeline_runs = _relationship('PipelineRun', 'sequencing_run')
    lanes = _relationship('SequencingLane', 'run')
    run_elements = _relationship('RunElement', 'run')


class SequencingLane(Base):
    __tablename__ = 'lanes'
    item_title = 'lane'

    run_id = Column(String, ForeignKey('sequencing_runs.run_id'), primary_key=True)
    run = _relationship('SequencingRun', 'lanes')
    lane_number = Column(Integer, primary_key=True)

    run_elements = _relationship('RunElement', 'sequencing_lane')
    unexpected_barcodes = _relationship('UnexpectedBarcode', 'sequencing_lane')


class Project(Base):
    __tablename__ = 'projects'
    reportable_fields = ('project_id',)

    project_id = Column(String, unique=True, primary_key=True)
    samples = _relationship('Sample', 'project')


class PipelineRun(Base):
    __tablename__ = 'pipeline_runs'
    reportable_fields = ('dataset_type', 'dataset_name', 'start_date')
    item_title = 'pipeline_run'

    dataset_type = Column(Enum(*dataset_types))
    dataset_name = Column(String, ForeignKey('sequencing_runs.run_id'), ForeignKey('samples.sample_id'), primary_key=True)
    start_date = Column(DateTime, primary_key=True)
    end_date = Column(DateTime)
    pid = Column(Integer, nullable=True)

    sequencing_run = _relationship('SequencingRun', 'pipeline_runs')
    sample = _relationship('Sample', 'pipeline_runs')
    stages = _relationship('PipelineStage', 'pipeline_run')


class PipelineStage(Base):
    __tablename__ = 'pipeline_stages'
    reportable_fields = ('dataset_type', 'dataset_name', 'stage_name')
    item_title = 'pipeline_stage'

    pipeline_id = Column(String, ForeignKey('pipeline_runs.id'), primary_key=True)
    stage_name = Column(String, primary_key=True)

    start_date = Column(DateTime)
    end_date = Column(DateTime)
    exit_status = Column(Integer, nullable=True)

    pipeline_run = _relationship('PipelineRun', back_populates='stages')
