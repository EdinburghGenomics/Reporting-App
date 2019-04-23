import os
import re
import yaml
import datetime
from cached_property import cached_property
from egcg_core.clarity import connection, get_sample
from egcg_core.constants import ELEMENT_REVIEW_COMMENTS, ELEMENT_REVIEW_DATE, ELEMENT_REVIEWED
from egcg_core.util import query_dict
from eve.methods.patch import patch_internal
from eve.methods.get import get
from werkzeug.datastructures import ImmutableMultiDict
from werkzeug.exceptions import abort
from flask import request
from config import rest_config
from rest_api import settings
from rest_api.actions.reviews import Action

cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'etc', 'review_thresholds.yaml')
review_thresholds = yaml.safe_load(open(cfg_path, 'r'))


class AutomaticReviewer:
    reviewable_data = None
    opposite = {'>': '<', '<': '>'}

    @staticmethod
    def eve_get(*args, **kwargs):
        res = get(*args, **kwargs)
        data = res[0].get('data')
        next_page = query_dict(res[0], '_links.next')
        # depaginate recursively
        if next_page:
            match = re.match('\w+\?page=(\d+)', next_page.get('href'))
            previous_args = request.args
            # inject page number in the args of the request to allow eve to pick it up
            request.args = ImmutableMultiDict({'page': int(match.group(1))})
            data.extend(AutomaticReviewer.eve_get(*args, **kwargs))
            # restore the args that was there previously
            request.args = previous_args
        return data

    @cached_property
    def current_time(self):
        return datetime.datetime.now().strftime(settings.DATE_FORMAT)

    @property
    def cfg(self):
        raise NotImplementedError

    @staticmethod
    def resolve_formula(data, formula):
        modif_formula = formula
        for word in re.findall('[\w.]+', formula):
            value = query_dict(data, word)
            if value:
                modif_formula = modif_formula.replace(word, str(value))
        try:
            return eval(modif_formula)
        except NameError:
            return None

    @cached_property
    def failing_metrics(self):
        passfails = {}

        for metric in self.cfg:
            # resolve the formula if it exist otherwise resolve from the name of the metric
            if 'formula' in self.cfg[metric]:
                metric_value = self.resolve_formula(self.reviewable_data, self.cfg[metric]['formula'])
            else:
                metric_value = query_dict(self.reviewable_data, metric)
            comparison = self.cfg[metric]['comparison']
            compare_value = self.cfg[metric]['value']

            check = None
            if metric_value is None:
                check = False

            elif comparison == '>':
                check = metric_value >= compare_value

            elif comparison == '<':
                check = metric_value <= compare_value

            passfails[metric] = 'pass' if check else 'fail'

        return sorted(k for k, v in passfails.items() if v == 'fail')

    @property
    def failure_comment(self):
        return 'Failed due to ' + ', '.join(['%s %s %s' % (
            self.cfg.get(f, {}).get('name', f),
            self.opposite.get(self.cfg.get(f, {}).get('comparison')),
            self.cfg.get(f, {}).get('value')
        ) for f in self.failing_metrics])

    @cached_property
    def _summary(self):
        if self.failing_metrics:
            return {
                ELEMENT_REVIEWED: 'fail',
                ELEMENT_REVIEW_COMMENTS: self.failure_comment,
                ELEMENT_REVIEW_DATE: self.current_time,
            }
        else:
            return {
                ELEMENT_REVIEWED: 'pass',
                ELEMENT_REVIEW_COMMENTS: 'pass',
                ELEMENT_REVIEW_DATE: self.current_time,
            }


class AutomaticLaneReviewer(AutomaticReviewer):
    def __init__(self, lane_metrics):
        self.reviewable_data = lane_metrics
        self.run_id = lane_metrics['run_id']
        self.lane_number = lane_metrics['lane_number']

    @property
    def cfg(self):
        return review_thresholds['lane']

    @property
    def run_elements(self):
        return self.eve_get('run_elements', run_id=self.run_id, lane=self.lane_number)

    def push_review(self):
        for re in self.run_elements:
            if re.get('barcode'):
                patch_internal(
                    'run_elements',
                    payload=self._summary,
                    run_id=self.run_id,
                    lane=re.get('lane'),
                    barcode=re.get('barcode')
                )
            else:
                patch_internal(
                    'run_elements',
                    payload=self._summary,
                    run_id=self.run_id,
                    lane=re.get('lane')
                )


class AutomaticRunReviewer(Action, AutomaticReviewer):
    def __init__(self, request):
        super().__init__(request)
        self.run_id = self.request.form.get('run_id')

        lanes = self.eve_get('lanes', run_id=self.run_id)
        if not lanes:
            abort(404, 'No data found for run id %s.' % self.run_id)
        self.lane_reviewers = [AutomaticLaneReviewer(lane) for lane in lanes]

    def _perform_action(self):
        for reviewer in self.lane_reviewers:
            reviewer.push_review()
        return {
            'action_id': self.run_id + self.date_started,
            'date_finished': self.now(),
            'action_info': {
                'run_id': self.run_id
            }
        }


class AutomaticRapidSampleReviewer(Action, AutomaticReviewer):
    def __init__(self, request):
        super().__init__(request)
        self.sample_id = self.request.form['sample_id']

    @property
    def cfg(self):
        return review_thresholds['rapid']

    @cached_property
    def reviewable_data(self):
        data = self.eve_get('samples', sample_id=self.sample_id)
        if data and 'rapid_analysis' in data[0]:
            return data[0]
        else:
            abort(404, 'No data found for sample id %s.' % self.sample_id)

    def _perform_action(self):
        payload = self.reviewable_data.get('rapid_analysis')  # patch with the whole subdict, or it gets overwritten

        if self.failing_metrics:
            payload[ELEMENT_REVIEWED] = 'fail'
            payload[ELEMENT_REVIEW_COMMENTS] = self.failure_comment
        else:
            payload[ELEMENT_REVIEWED] = 'pass'

        payload[ELEMENT_REVIEW_DATE] = self.current_time

        patch_internal(
            'samples',
            {'rapid_analysis': payload},
            sample_id=self.sample_id
        )

        return {
            'action_id': self.sample_id + self.date_started,
            'date_finished': self.now(),
            'action_info': {
                'sample_id': self.sample_id
            }
        }


class AutomaticSampleReviewer(Action, AutomaticReviewer):
    def __init__(self, request):
        Action.__init__(self, request)
        self.sample_id = self.request.form.get('sample_id')

    @cached_property
    def lims_sample(self):
        connection(new=True, **rest_config.get('clarity'))
        s = get_sample(self.sample_id)
        if not s:
            abort(404, 'Sample %s cannot be found in the Lims' % self.sample_id)
        return s

    @cached_property
    def reviewable_data(self):
        data = self.eve_get('samples', sample_id=self.sample_id)
        if data:
            return data[0]
        else:
            abort(404, 'No data found for sample id %s.' % self.sample_id)

    @property
    def sample_genotype(self):
        return self.reviewable_data.get('genotype_validation')

    @property
    def species(self):
        return self.reviewable_data.get('species_name')

    def find_value(self, db_key, lims_key):
        value = self.reviewable_data.get(db_key)
        if not value:
            value = self.lims_sample.udf.get(lims_key)
        return value

    @cached_property
    def cfg(self):
        cfg = review_thresholds['sample'].get(self.species, {}).copy()
        cfg.update(review_thresholds['sample']['default'])

        if self.sample_genotype is None:
            cfg.pop('genotype_validation.mismatching_snps', None)
            cfg.pop('genotype_validation.no_call_seq', None)

        required_yield = self.reviewable_data.get('required_yield')
        if not required_yield:
            required_yield = self.lims_sample.udf.get('Required Yield (Gb)')
        else:
            # Convert in Gb
            required_yield = int(required_yield / 1000000000)
        if not required_yield:
            abort(404, 'Sample %s does not have a expected yield' % self.sample_id)

        coverage = self.find_value('required_coverage', 'Coverage (X)')
        if not coverage:
            abort(404, 'Sample %s does not have a target coverage' % self.sample_id)

        cfg['aggregated.clean_yield_in_gb']['value'] = required_yield
        cfg['coverage.mean']['value'] = coverage
        return cfg

    @cached_property
    def _summary(self):
        summary = super()._summary
        if self.species == 'Homo sapiens' and self.sample_genotype is None:
            summary[ELEMENT_REVIEWED] = 'genotype missing'
            summary[ELEMENT_REVIEW_COMMENTS] = 'Failed due to missing genotype'
        return summary

    def push_review(self):
        patch_internal(
            'samples',
            payload=self._summary,
            sample_id=self.sample_id
        )

    def _perform_action(self):
        self.push_review()
        return {
            'action_id': self.sample_id + self.date_started,
            'date_finished': self.now(),
            'action_info': {
                'sample_id': self.sample_id
            }
        }
