import json
import datetime
from egcg_core import clarity
from pyclarity_lims.entities import Queue, Step
from requests.exceptions import HTTPError
from werkzeug.exceptions import abort

from rest_api import settings
from rest_api.aggregation.database_side import db
from config import rest_config as cfg


class ReviewInitiator:
    lims_workflow_name = 'PostSeqLab EG 1.0 WF'
    populate_artifacts_epp_name = 'Upload metrics and assess samples'
    lims_step_name = None

    def __init__(self, request):
        self.sample_ids_to_review = json.loads(request.form.get('review_entities'))
        self.username = request.form.get('username')
        self.password = request.form.get('password')
        self._lims = None
        self._stage = None
        self._artifacts_to_review = None

    @property
    def lims(self):
        if self._lims is None:
            try:
                self._lims = clarity.connection(new=True, username=self.username, password=self.password, **cfg.get('clarity'))
                self._lims.get(self._lims.get_uri())
            except HTTPError:
                abort(401, 'Authentication in the LIMS (%s) failed' % cfg.get('clarity', {}).get('baseuri'))
        return self._lims

    @property
    def samples_to_review(self):
        try:
            # Retrieve the samples from the LIMS
            samples_to_review = clarity.get_list_of_samples(list(self.sample_ids_to_review))
        except HTTPError:
            samples_to_review = []

        if len(samples_to_review) != len(self.sample_ids_to_review):
            abort(
                409,
                'Some of the samples to review were not found in the LIMS. %s samples requested %s samples found' % (
                    len(self.sample_ids_to_review), len(samples_to_review)
                )
            )
        return samples_to_review

    @property
    def stage(self):
        if self._stage is None:
            self._stage = clarity.get_workflow_stage(workflow_name=self.lims_workflow_name, stage_name=self.lims_step_name)
        return self._stage

    def artifact_replicates(self, artifacts):
        return 1

    @staticmethod
    def now():
        return datetime.datetime.now().strftime(settings.DATE_FORMAT)

    def start_review(self):
        queue = Queue(self.lims, id=self.stage.step.id)
        samples_queued = set()
        artifacts_to_review = []

        # find all samples that are queued and to review
        artifacts = queue.artifacts
        for a in artifacts:
            if len(a.samples) != 1:
                abort(409, 'Artifact %s Queued on %s contains more than one sample' % (a.name, self.lims_step_name))
            if a.samples[0].name in self.sample_ids_to_review:
                artifacts_to_review.append(a)
            samples_queued.add(a.samples[0])

        # find all samples that are to review but not queued
        samples_to_review_but_not_queued = set(self.samples_to_review).difference(samples_queued)
        if samples_to_review_but_not_queued:
            artifacts = [s.artifact for s in samples_to_review_but_not_queued]
            # Queue the artifacts that were not already there
            self.lims.route_artifacts(artifact_list=artifacts, stage_uri=self.stage.uri)
            artifacts_to_review.extend(artifacts)

        if len(artifacts_to_review) != len(self.sample_ids_to_review):
            abort(
                409,
                'Could not find artifacts for all samples. Requested %s samples, found %s artifacts' % (
                    len(self.sample_ids_to_review), len(artifacts_to_review)
                )
            )

        # Create a new step from the queued artifacts
        # with the number of replicates that correspond to the number of run elements
        s = Step.create(
            self.lims,
            protocol_step=self.stage.step,
            inputs=artifacts_to_review,
            replicates=self.artifact_replicates(artifacts_to_review)
        )

        if self.populate_artifacts_epp_name in s.program_names:
            s.trigger_program(self.populate_artifacts_epp_name)

        # build the returned json
        return {
            'action_id': 'lims_' + s.id,
            'started_by': self.username,
            'date_started': self.now(),
            'action_info': {
                'lims_step_name': self.lims_step_name,
                'lims_url': cfg['clarity']['baseuri'] + '/clarity/work-details/' + s.id.split('-')[1],
                'samples': self.sample_ids_to_review
            }
        }


class RunReviewInitiator(ReviewInitiator):
    lims_step_name = 'Sequencer Output Review EG 1.0 ST'

    def artifact_replicates(self, artifacts):
        # Get the number of run elements for each sample directly from the database.
        run_element_counts = {}
        for sample_id in self.sample_ids_to_review:
            run_element_counts[sample_id] = db['run_elements'].count({'sample_id': sample_id})

        return [run_element_counts.get(a.samples[0].name) for a in artifacts]


class SampleReviewInitiator(ReviewInitiator):
    lims_step_name = 'Sample Review EG 1.0 ST'
