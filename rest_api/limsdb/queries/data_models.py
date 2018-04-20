import operator
from datetime import datetime
from collections import defaultdict
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
        This function is a bit overcomplicated !!! but bare with me while I try to explain.
        The goal is to extract the all the statuses this sample had and the LIMS processes that had gone
        though during those status.
        The relationship between process and statuses is defined by the config file project_status_definitions.yaml.
        We start by sorting all the processes by date from the oldest to the most recent, then iterate and get the
        status associated with each process. Processes not associated with a status will associated with the most
        recent status encountered.
        For completed process we associate them with the last status seen but the queued process get assotiated with
        the status defined by the current process.
        """

        def add_process_with_status(status_order, process_per_status, status, process):
            if status_order and status_order[-1] == status:
                process_per_status[-1].append(process)
            else:
                status_order.append(status)
                process_per_status.append([process])

        if not self._all_statuses_and_date:
            self._all_statuses_and_date = []
            processes_per_status = []  # Contains lists of processes stored in the same order as  status in status_order
            status_order = []  # Contains a list of status ordered chronologically.
            current_status = status = status_cfg.status_order[0]
            for process, date, process_type, process_id in sorted(self._processes, key=operator.itemgetter(1)):

                process_dict = {'name': process,
                                'date': date.strftime('%b %d %Y'),
                                'type': process_type,
                                'process_id': process_id}
                # This part find the new status
                if process_type == 'complete' and process in status_cfg.step_completed_to_status:
                    status = status_cfg.step_completed_to_status.get(process)
                elif process_type in ['queued', 'progress'] and process in status_cfg.step_queued_to_status:
                    status = status_cfg.step_queued_to_status.get(process)

                # Associate the process with the last status seen
                if process_type == 'complete':
                    add_process_with_status(status_order, processes_per_status, current_status, process_dict)
                # Associate the process with the status defined by the current process
                else:
                    add_process_with_status(status_order, processes_per_status, status, process_dict)
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
        if self.status == status_cfg.status_names['FINISHED']:
            return self.status_date
        return None

    def to_json(self):
        return {
            'sample_id': self.sample_name,
            'project_id': self.project_name,
            'statuses': self.all_statuses(),
            'current_status': self.status,
            'started_date': format_date(self.started_date),
            'finished_date': format_date(self.finished_date),
            'library_type': self.library_type,
            'species': self.species
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

    @property
    def library_types(self):
        return ', '.join(set(sample.library_type for sample in self.samples if sample.library_type))

    @property
    def species(self):
        return ', '.join(set(sample.species for sample in self.samples if sample.species))

    def to_json(self):
        ret = {
            'plate_id': self.container_name,
            'project_id': self.project_id,
            'nb_samples': len(self.samples),
            'library_type': self.library_types,
            'species': self.species
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