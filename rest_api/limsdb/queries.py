from collections import defaultdict, OrderedDict

import genologics_sql.tables as t

SAMPLE_SUB_STEPS = [set(['Receive Sample 4.0']), set(['Receive Sample EG 6.1'])]
SAMPLE_QC_STEPS = [set(['Eval Project Quant'])]
LIBRARY_PREP_STEPS = [set(['Read and Eval SSQC'])]
LIBRARY_QC_STEPS = [set(['Eval qPCR Quant'])]
SEQUENCING_STEPS = [set(['AUTOMATED - Sequence'])]
BIOINFORMATICS_STEPS = [set(['bioinformatics'])]
DELIVERY_STEPS = [set(['Data Release EG 1.0'])]
sample_statuses = OrderedDict((
    ('Sample Submission', SAMPLE_SUB_STEPS),
    ('Sample QC', SAMPLE_QC_STEPS),
    ('Library Preparation', LIBRARY_PREP_STEPS),
    ('Library QC', LIBRARY_QC_STEPS),
    ('Sequencing', SEQUENCING_STEPS),
    ('Bioinformatics', BIOINFORMATICS_STEPS),
    ('Delivery', DELIVERY_STEPS),
    ('Finished', [])
))


def get_samples_and_processes(session, project_name=None, list_process=None, workstatus=None, only_open_project=True):
    """This method runs a query that return the sample name and the processeses they went through"""
    q = session.query(t.Project.name, t.Project.opendate, t.Researcher.firstname, t.Researcher.lastname,
                      t.Sample.name, t.ProcessType.displayname, t.Process.workstatus)\
           .distinct(t.Sample.name, t.Process.processid) \
           .join(t.Sample.project) \
           .join(t.Project.researcher) \
           .join(t.Sample.artifacts)\
           .join(t.Artifact.processiotrackers)\
           .join(t.ProcessIOTracker.process)\
           .join(t.Process.type)
    if list_process:
        q = q.filter(t.ProcessType.displayname.in_(list_process))
    if project_name:
        q = q.filter(t.Project.name == project_name)
    if workstatus:
        q = q.filter(t.Process.workstatus == workstatus)
    if only_open_project:
        q = q.filter(t.Project.closedate == None)
    return q.all()

def non_QC_queues(session, project_name=None, sample_name=None, list_process=None):
    """
    This query gives all of the samples sitting in queue of a aledgedly non-qc steps
    """
    q = session.query(
        t.Project.name, t.Sample.name, t.ProcessType.displayname
    )
    q = q.distinct(
        t.Project.name, t.Sample.name, t.ProcessType.displayname
    )
    q = q.join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.stage_transitions) \
        .join(t.StageTransition.stage) \
        .join(t.Stage.protocolstep) \
        .join(t.ProtocolStep.processtype) \
        .join(t.Stage.workflowsection) \
        .join(t.WorkflowSection.labprotocol) \
        .join(t.WorkflowSection.labworkflow)
    q = q.order_by(t.Project.name, t.Sample.name, t.LabProtocol.protocolname)
    if project_name:
        q = q.filter(t.Project.name == project_name)
    if sample_name:
        q = q.filter(t.Sample.name == sample_name)
    if list_process:
        q = q.filter(t.ProcessType.displayname.in_(list_process))
    # StageTransition.workflowrunid is positive when the transition in not complete and negative when the transition is completed
    q = q.filter(t.StageTransition.workflowrunid > 0)
    q = q.filter(t.StageTransition.completedbyid.is_(None))
    return q.all()



class Sample():
    def __init__(self):
        self.processes = set()
        self.unfinished_processes = set()


    def finished_steps(self):
        fs = []
        for status in sample_statuses:
            match = False
            for steps_to_match in sample_statuses.get(status):
                if steps_to_match.issubset(self.processes):
                    match = True
                    break
            if match:
                fs.append(status)

        return fs

    @property
    def next_step(self):
        finished_steps = self.finished_steps()
        all_steps = list(sample_statuses.keys())
        if finished_steps:
            return all_steps[all_steps.index(finished_steps[-1]) + 1]
        else:
            return all_steps[0]

class Project():
    def __init__(self):
        self.samples = defaultdict(Sample)
        self.open_date = None
        self.researcher_name = None

    def samples_per_status(self):
        sample_per_status = defaultdict(list)
        for sample_name in self.samples:
            sample_per_status[self.samples[sample_name].next_step].append(sample_name)
        return sample_per_status

def sample_status_per_project(session, project_name=None):
    all_projects = defaultdict(Project)
    for result in get_samples_and_processes(session, project_name, workstatus='COMPLETE'):
        project_name, open_date, firstname, lastname, sample_name, process_name, process_status = result
        all_projects[project_name].samples[sample_name].processes.add(process_name)
        all_projects[project_name].open_date = open_date.isoformat() + 'Z'
        all_projects[project_name].researcher_name = '%s %s'%(firstname, lastname)

    res = []
    for project_name in all_projects:
        project = {
            'project_id': project_name,
            'open_date': all_projects[project_name].open_date,
            'researcher_name': all_projects[project_name].researcher_name
        }
        project.update(all_projects[project_name].samples_per_status())
        res.append(project)
    return res

def all_processes_per_project(session, project_name=None):
    all_projects = defaultdict(dict)
    all_processes = set()
    for result in get_samples_and_processes(session, project_name, workstatus='COMPLETE'):
        project_name, sample_name, process_name, process_status = result
        all_processes.add(process_name)
        if not process_name in all_projects[project_name]:
            all_projects[project_name][process_name] = set()
        all_projects[project_name][process_name].add(sample_name)

    all_processes = sorted(list(all_processes))
    columns = ['Project'] + all_processes
    rows = []
    for project in all_projects:
        row = [project]
        for process_name in all_processes:
            row.append(str(len(all_projects[project].get(process_name, []))))
        rows.append(row)
    return {'title':'Processes', 'cols':columns, 'rows':rows}
