from collections import defaultdict
from flask import request, json
from egcg_core.clarity import sanitize_user_id
from rest_api.limsdb import queries


class Sample:
    def __init__(self):
        self.sample_name = None
        self.project_name = None
        self.plate_name = None
        self.original_name = None
        self.udfs = {}

    def to_json(self):
        to_return = {
            'sample_id': self.sample_name,
            'project_id': self.project_name,
            'plate_id': self.plate_name,
        }
        to_return.update(self.udfs)
        return to_return


def _create_samples(session):
    """This function queries the lims database for sample information and create Sample objects"""
    match = json.loads(request.args.get('match', '{}'))
    all_samples = defaultdict(Sample)
    project_id = match.get('project_id')
    sample_id = match.get('sample_id')

    for result in queries.get_sample_info(session, project_id, sample_id, udfs='all'):
        (pjct_name, sample_name, container, wellx, welly, udf_name, udf_value) = result
        s = all_samples[sanitize_user_id(sample_name)]
        s.sample_name = sanitize_user_id(sample_name)
        s.project_name = pjct_name
        s.plate_name = container
        s.original_name = sample_name
        s.udfs[udf_name] = udf_value

    return all_samples.values()


def sample_info(session, app):
    """This function queries the lims database for sample information and return json representation"""
    samples = _create_samples(session)
    return [s.to_json() for s in samples]
