import operator
from datetime import datetime
from collections import defaultdict
from cached_property import cached_property
from config import project_status as status_cfg
from rest_api.limsdb.queries import format_date


class SampleInfo:
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


class ProjectInfo:

    def __init__(self):
        self.project_id = None
        self.open_date = None
        self.close_date = None
        self.researcher_name = None
        self.nb_quoted_samples = None

    @property
    def status(self):
        if self.close_date:
            return 'closed'
        else:
            return 'open'

    def to_json(self):
        ret = {
            'project_id': self.project_id,
            'open_date': format_date(self.open_date),
            'close_date': format_date(self.close_date),
            'project_status': self.status,
            'researcher_name': self.researcher_name,
            'nb_quoted_samples': self.nb_quoted_samples,
        }
        return ret


class Sample(SampleInfo):
    def __init__(self):
        super().__init__()
        self._processes = set()
        self._status_and_date = None
        self._all_statuses_and_date = None
        self.planned_library = None
        self.species = None
        self.required_yield = None
        self.coverage = None

    def add_completed_process(self, process_name, completed_date, process_id=None):
        self._processes.add((process_name, completed_date, 'complete', process_id))
        self._status_and_date = self._all_statuses_and_date = None

    def add_queue_location(self, process_name, queued_date, queue_id=None):
        self._processes.add((process_name, queued_date, 'queued', queue_id))
        self._status_and_date = self._all_statuses_and_date = None

    def add_inprogress(self, process_name, last_update_date, process_id=None):
        self._processes.add((process_name, last_update_date, 'progress', process_id))

    @property
    def processes(self):
        return sorted(self._processes, key=operator.itemgetter(1), reverse=True)

    def all_statuses(self):
        """
        Extract all the statuses this sample has had and the LIMS processes run during those statuses.

        The relationships between processes and statuses is defined by the config file project_status_definitions.yaml.
        We start by sorting all the processes by date from the oldest to the most recent, then iterate and get the
        status associated with each process. Processes not associated with a status will be associated with the most
        recent status encountered. We associate completed processes with the last status seen, but processes queued or
        in progress get associated with the status defined by the current process.
        """

        def add_process_with_status(status_order, process_per_status, status, process):
            if status_order and status_order[-1] == status:
                process_per_status[-1].append(process)
            else:
                status_order.append(status)
                process_per_status.append([process])

        if not self._all_statuses_and_date:
            self._all_statuses_and_date = []
            processes_per_status = []  # Contains lists of processes stored in the same order as status_order
            status_order = []  # Contains a list of statuses ordered chronologically
            current_status = status = status_cfg.status_order[0]
            for process, date, process_type, process_id in sorted(self._processes, key=operator.itemgetter(1)):
                process_info = {
                    'name': process, 'date': date.strftime('%b %d %Y'), 'type': process_type, 'process_id': process_id
                }

                # Find the new status
                if process_type == 'complete' and process in status_cfg.step_completed_to_status:
                    status = status_cfg.step_completed_to_status.get(process)
                elif process_type in ['queued', 'progress'] and process in status_cfg.step_queued_to_status:
                    status = status_cfg.step_queued_to_status.get(process)

                # Associate the process with the last status seen...
                if process_type == 'complete':
                    add_process_with_status(status_order, processes_per_status, current_status, process_info)
                # ... or with the status it defines
                else:
                    add_process_with_status(status_order, processes_per_status, status, process_info)

                current_status = status

            for i, status in enumerate(status_order):
                self._all_statuses_and_date.append({
                    'name': status,
                    'date': processes_per_status[i][0]['date'],
                    'processes': processes_per_status[i]
                })
        return self._all_statuses_and_date

    def _get_status_and_date(self):
        if not self._status_and_date:
            status = None
            self._status_and_date = status_cfg.status_order[0], datetime.now()
            for process, date, process_type, process_id in self.processes:
                new_status = None
                if process_type == 'complete' and process in status_cfg.step_completed_to_status:
                    new_status = status_cfg.step_completed_to_status.get(process)
                elif process_type in ['queued', 'progress'] and process in status_cfg.step_queued_to_status:
                    new_status = status_cfg.step_queued_to_status.get(process)
                if not status:
                    status = new_status
                    self._status_and_date = (status, date)
                elif status == new_status:
                    self._status_and_date = (status, date)
                else:
                    break
        return self._status_and_date

    @property
    def additional_status(self):
        additional_status = set()
        for process, date, process_type, process_id in self.processes:
            if process_type == 'complete' and process in status_cfg.additional_step_completed:
                finished_status = status_cfg.additional_step_completed.get(process)
                # A sample should not appear in invoiced if it has been removed, as this is paradoxical
                if self.status != 'removed' or finished_status != 'invoiced':
                    additional_status.add(finished_status)
        return additional_status

    @property
    def library_type(self):
        for process, date, process_type, process_id in self.processes:
            if process_type == 'complete' and process in status_cfg.library_type_step_completed:
                return status_cfg.library_type_step_completed.get(process)
        return status_cfg.library_planned_alias.get(self.planned_library)

    @property
    def status(self):
        status, date = self._get_status_and_date()
        return status

    @property
    def status_date(self):
        status, date = self._get_status_and_date()
        return date

    @property
    def started_date(self):
        """Date of the first completed step"""
        for p in reversed(self.processes):
            process, date, process_type, process_id = p
            if process_type == 'complete' and process in status_cfg.started_steps:
                return date

    @property
    def finished_date(self):
        """Date of the first step marking as finished"""
        for p in reversed(self.processes):
            process, date, process_type, process_id = p
            if process_type == 'complete' and process in status_cfg.finished_steps:
                return date

    def to_json(self):
        return {
            'sample_id': self.sample_name,
            'project_id': self.project_name,
            'statuses': self.all_statuses(),
            'current_status': self.status,
            'started_date': format_date(self.started_date),
            'finished_date': format_date(self.finished_date),
            'library_type': self.library_type,
            'species': self.species,
            'required_yield': self.required_yield,
            'required_coverage': self.coverage
        }


class Container:
    def __init__(self):
        self.samples = []
        self.project_id = None
        self.container_name = None

    def samples_per_status(self):
        sample_per_status = defaultdict(list)
        for sample in self.samples:
            sample_per_status[sample.status].append(sample.sample_name)
            for status in sample.additional_status:
                sample_per_status[status].append(sample.sample_name)
        return sample_per_status

    def _extract_from_samples(self, field):
        return ', '.join(sorted(set(getattr(sample, field) for sample in self.samples if getattr(sample, field))))

    @property
    def coverage(self):
        return self._extract_from_samples('coverage')

    @property
    def required_yield(self):
        return self._extract_from_samples('required_yield')

    @property
    def library_types(self):
        return self._extract_from_samples('library_type')

    @property
    def species(self):
        return self._extract_from_samples('species')

    def to_json(self):
        ret = {
            'plate_id': self.container_name,
            'project_id': self.project_id,
            'nb_samples': len(self.samples),
            'library_type': self.library_types,
            'species': self.species,
            'required_yield': self.required_yield,
            'required_coverage': self.coverage
        }
        ret.update(self.samples_per_status())
        return ret


class Project(Container, ProjectInfo):
    def __init__(self):
        # Explicitly call parent constructors
        Container.__init__(self)
        ProjectInfo.__init__(self)

    def to_json(self):
        ret = {
            'project_id': self.project_id,
            'nb_samples': len(self.samples),
            'library_type': self.library_types,
            'required_yield': self.required_yield,
            'required_coverage': self.coverage,
            'species': self.species,
            'open_date': format_date(self.open_date),
            'close_date': format_date(self.close_date),
            'project_status': self.status,
            'researcher_name': self.researcher_name,
            'nb_quoted_samples': self.nb_quoted_samples,
            'finished_date': format_date(self.finished_date),
            'started_date': format_date(self.started_date)
        }
        ret.update(self.samples_per_status())
        return ret

    @property
    def finished_date(self):
        finished_dates = [
                sample.status_date
                for sample in self.samples
                if sample.status == status_cfg.status_names['FINISHED']
            ]
        if finished_dates and self.nb_quoted_samples and len(finished_dates) >= int(self.nb_quoted_samples):
            finished_dates.sort()
            return finished_dates[-1]
        return None

    @property
    def started_date(self):
        if self.samples:
            started_dates = sorted(sample.started_date for sample in self.samples if sample.started_date)
            if started_dates:
                return started_dates[0]
        return None


class Run:
    def __init__(self):
        self.created_date = None
        self.cst_date = None
        self.udfs = {}
        self.samples = set()
        self.projects = set()

    def to_json(self):
        return {
            'created_date': format_date(self.created_date),
            'cst_date': format_date(self.cst_date),
            'run_id': self.udfs['RunID'],
            'run_status': self.udfs['Run Status'],
            'sample_ids': sorted(list(self.samples)),
            'project_ids': sorted(list(self.projects)),
            'instrument_id': self.udfs['InstrumentID'],
            'nb_reads': self.udfs['Read'],
            'nb_cycles': self.udfs['Cycle']
        }


class LibraryPreparation:
    def __init__(self):
        self.id = None
        self.type = None
        self.qpcrs = defaultdict(QPCR)

    def to_json(self):
        most_recent_qpcr = sorted(self.qpcrs.values(), key=lambda p: p.date_run, reverse=True)[0]
        projects = set()
        data = {
            'id': self.id,
            'qpcrs_run': len(self.qpcrs),
            'date_completed': format_date(most_recent_qpcr.date_run),
            'placements': {},
            'type': status_cfg.protocol_names.get(self.type, 'unknown'),
            'nsamples': len(most_recent_qpcr.placements)
        }

        passing_samples = 0
        for k, v in most_recent_qpcr.placements.items():
            projects.add(v.project_id)
            data['placements']['%s:%s' % k] = v.to_json()
            if v.qc_flag == 'PASSED':
                passing_samples += 1

        data['pc_qc_flag_pass'] = (passing_samples / len(most_recent_qpcr.placements)) * 100
        data['project_ids'] = sorted(projects)
        return data


class QPCR:
    def __init__(self):
        self.id = None
        self.date_run = None
        self.placements = defaultdict(Library)


class Library:
    state_map = {
        0: 'UNKNOWN',
        1: 'PASSED',
        2: 'FAILED'
    }

    def __init__(self):
        self.name = None
        self.library_qc = {}
        self.states = {}
        self.project_id = None

    @cached_property
    def qc_flag(self):
        """Duplicates functionality in genologics_sql.tables.Artifact.qc_flag"""
        if not self.states:
            return None

        k = sorted(self.states)[-1]
        latest_state = self.states[k]
        return self.state_map.get(latest_state, 'ERROR')

    def to_json(self):
        return {
            'name': self.name,
            'library_qc': self.library_qc,
            'qc_flag': self.qc_flag,
            'project_id': self.project_id
        }
