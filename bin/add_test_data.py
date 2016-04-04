import random
import datetime
import sqlalchemy.orm
from sqlalchemy import create_engine, func
from rest_api import model


def _random_string(length):
    chars = 'qwertyuiopasdfghjklzxcvbnm1234567890'
    return ''.join((random.choice(chars) for _ in range(length)))


def _random_int(minimum=200, maximum=800):
    return random.randint(minimum, maximum)


def _random_float(magnitude=3, round_to=2):
    n = random.random()
    for _ in range(magnitude):
        n *= 10
    return round(n, round_to)


def _new(cls, **kwargs):
    bts_params = {
        'id': _random_string(24),
        '_etag': _random_string(40),
        '_created': func.now(),
        '_updated': func.now()
    }
    kwargs.update(bts_params)
    return cls(**kwargs)


def _multinew(cls, cols, data, **global_params):
    entities = []
    ncols = len(cols)

    for d in data:
        assert len(d) == ncols
        config = dict(zip(cols, d))
        config.update(global_params)
        entities.append(_new(cls, **config))
    return entities


def add_test_data():
    time_1_1 = datetime.datetime(2016, 3, 29, 9, 0, 0)
    time_1_2 = datetime.datetime(2016, 3, 29, 9, 10, 0)
    time_2_1 = datetime.datetime(2016, 3, 30, 9, 0, 0)
    time_2_2 = datetime.datetime(2016, 3, 30, 9, 10, 0)

    i = _random_int
    f = _random_float

    run_elements = _multinew(
        model.RunElement,
        (
            'run_id', 'lane_number', 'barcode', 'project_id', 'sample_id', 'library_id',
            'passing_filter_reads', 'pc_reads_in_lane', 'total_reads', 'bases_r1', 'q30_bases_r1', 'bases_r2',
            'q30_bases_r2', 'adaptor_bases_removed_r1', 'adaptor_bases_removed_r2', 'clean_reads',
            'clean_bases_r1', 'clean_q30_bases_r1', 'clean_bases_r2', 'clean_q30_bases_r2',
            'fastqc_report_r1', 'fastqc_report_r2', 'reviewed', 'useable'
        ),
        (
            ('run_1', 1, 'AAAAAAAA', 'project_1', 'sample_1', 'library_1', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None),
            ('run_1', 2, 'AAAAAAAT', 'project_1', 'sample_1', 'library_2', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None),
            ('run_1', 3, 'AAAAAAAC', 'project_1', 'sample_2', 'library_3', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None),
            ('run_2', 1, 'AAAAAAAA', 'project_1', 'sample_2', 'library_4', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None),
            ('run_2', 2, 'AAAAAAAT', 'project_2', 'sample_3', 'library_5', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None),
            ('run_2', 3, 'AAAAAAAC', 'project_2', 'sample_3', 'library_6', i(), f(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), i(), 'report_1.fastqc', 'report_2.fastqc', 'passed', None)
        )
    )

    unexpected_barcodes = _multinew(
        model.UnexpectedBarcode,
        ('run_id', 'lane_number', 'barcode', 'passing_filter_reads', 'pc_reads_in_lane'),
        (
            ('run_1', 1, 'CCCCCCCC', i(), f()),
            ('run_2', 1, 'CCCCCCCC', i(), f())
        )
    )

    samples = _multinew(
        model.Sample,
        (
            'sample_id', 'user_sample_id', 'library_id', 'project_id', 'bam_file_reads', 'mapped_reads',
            'properly_mapped_reads', 'duplicate_reads', 'median_coverage', 'pc_callable', 'freemix',
            'called_gender', 'provided_gender', 'reviewed', 'useable', 'delivered', 'input_fastqs_deleted'
        ),
        (
            ('sample_1', 'user_sample_1', 'library_1', 'project_1', i(), i(), i(), i(), f(), f(), f(), 'male', 'male', 'passed', None, False, False),
            ('sample_2', 'user_sample_2', 'library_2', 'project_1', i(), i(), i(), i(), f(), f(), f(), 'male', 'male', 'passed', None, False, False),
            ('sample_3', 'user_sample_3', 'library_3', 'project_2', i(), i(), i(), i(), f(), f(), f(), 'male', 'male', 'passed', None, False, False)
        )
    )

    sequencing_runs = _multinew(model.SequencingRun, ('run_id',), (('run_1',), ('run_2',)))

    projects = _multinew(model.Project, ('project_id',), (('project_1',), ('project_2',)))

    pipeline_runs = _multinew(
        model.PipelineRun,
        ('dataset_type', 'dataset_name', 'start_date', 'end_date', 'pid'),
        (
            ('sequencing_run', 'run_1',    time_1_1, time_2_2, i()),
            ('sequencing_run', 'run_1',    time_2_1, time_2_2, i()),
            ('sequencing_run', 'run_2',    time_1_1, time_2_2, i()),
            ('sample',         'sample_1', time_1_1, time_2_2, i()),
            ('sample',         'sample_2', time_1_1, time_2_2, i())
        )
    )

    pipeline_stages = _multinew(
        model.PipelineStage,
        ('pipeline_id', 'stage_name', 'start_date', 'end_date', 'exit_status'),
        (
            (pipeline_runs[0].id, 'stage_1', time_1_2, time_2_1, 0),
            (pipeline_runs[0].id, 'stage_2', time_1_2, time_2_1, 0),
            (pipeline_runs[1].id, 'stage_1', time_2_2, time_2_1, 1),
            (pipeline_runs[2].id, 'stage_1', time_1_2, time_2_1, 0),
            (pipeline_runs[3].id, 'stage_1', time_1_2, time_2_1, 1),
            (pipeline_runs[4].id, 'stage_1', time_1_2, time_2_1, 0)
        )
    )

    connection = create_engine('sqlite:////Users/mwham/workspace/sqlite/test').connect()
    session = sqlalchemy.orm.sessionmaker()(bind=connection)
    for e in (pipeline_runs, pipeline_stages, run_elements, samples, unexpected_barcodes, sequencing_runs, projects):
        session.add_all(e)

    session.commit()

    x = sequencing_runs[0]


if __name__ == '__main__':
    add_test_data()

'''
'INSERT INTO pipeline_runs '
(id, _created, _updated, _etag, dataset_type, dataset_name, start_date, end_date, pid)
'VALUES '
(?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?)
('n58hjntupyvtte5prs7xxseg', '2vh1o4k52keoolw412noz3609pu233b2bu10xu9d', 'run', 'run_1', '2016-03-29 09:00:00.000000', '2016-03-30 09:10:00.000000', 313),
('x2klizvmmftv0yt04v5rogbu', '52rfesrug3znl0p2w7m8rf1odfbaaugnxczeq05p', 'run', 'run_1', '2016-03-30 09:00:00.000000', '2016-03-30 09:10:00.000000', 272),
('zyjiafsr1wttd0ti87xfzqjm', 'f8rqit2g2gw8rox1qe11fcaip0zfayht6k8henpk', 'run', 'run_2', '2016-03-29 09:00:00.000000', '2016-03-30 09:10:00.000000', 322),
('pn9o41rck06svtblaktdope7', 'cqzov49fpyfpsp8olksox2ltpf2rqmrqb3r8kc88', 'sample', 'sample_1', '2016-03-29 09:00:00.000000', '2016-03-30 09:10:00.000000', 756),
('e94r04o7ic3ahizbutqw1sr0', 'lvhs52hpyilz6t5x5k1x32mjjvnmcizvpg7q01m4', 'sample', 'sample_2', '2016-03-29 09:00:00.000000', '2016-03-30 09:10:00.000000', 741))
'''
