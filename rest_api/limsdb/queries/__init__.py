from sqlalchemy import or_, and_, func
import genologics_sql.tables as t
from sqlalchemy.orm.util import aliased


def format_date(date):
    if date:
        return date.isoformat()
    return None


def add_filters(q, **kwargs):
    if kwargs.get('project_name'):
        q = q.filter(t.Project.name == kwargs.get('project_name'))
    if kwargs.get('sample_name'):
        q = q.filter(t.Sample.name == kwargs.get('sample_name'))
    if kwargs.get('list_process'):
        q = q.filter(t.ProcessType.displayname.in_(kwargs.get('list_process')))
    if kwargs.get('project_status'):
        if kwargs.get('project_status') == 'closed':
            q = q.filter(t.Project.closedate != None)
        elif kwargs.get('project_status') == 'open':
            q = q.filter(t.Project.closedate == None)
        elif kwargs.get('project_status') == 'all':
            # No filtering
            pass
        else:
            raise ValueError('Unknown value %s for project_status' % kwargs.get('project_status'))
    if kwargs.get('workstatus'):
        q = q.filter(t.Process.workstatus == kwargs.get('workstatus'))
    if kwargs.get('time_since'):
        q = q.filter(func.date(t.Sample.datereceived) > func.date(kwargs.get('time_since')))
    return q


def get_project_info(session, project_name=None, project_status='open', udfs=None):
    """This method runs a query that return the get projects and specific udfs"""
    q = session.query(t.Project.name, t.Project.opendate, t.Project.closedate, t.Researcher.firstname, t.Researcher.lastname,
                      t.EntityUdfView.udfname, t.EntityUdfView.udfvalue) \
        .distinct(t.Project.name) \
        .outerjoin(t.Project.researcher) \
        .outerjoin(t.Project.udfs)
    q = add_filters(q, project_name=project_name, project_status=project_status)
    if udfs:
        q = q.distinct(t.Project.name, t.EntityUdfView.udfname)
        q = q.filter(or_(t.EntityUdfView.udfname.in_(udfs), t.EntityUdfView.udfname == None))
    return q.all()


def get_sample_info(session, project_name=None, sample_name=None, project_status='open', time_since=None, udfs=None):
    """This method runs a query that return samples, its associated original container and some specified UDFs"""
    q = session.query(t.Project.name, t.Sample.name, t.Container.name,
                      t.ContainerPlacement.wellxposition, t.ContainerPlacement.wellyposition,
                      t.SampleUdfView.udfname, t.SampleUdfView.udfvalue) \
        .distinct(t.Sample.name) \
        .join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.containerplacement) \
        .join(t.ContainerPlacement.container) \
        .outerjoin(t.Sample.udfs)
    if udfs:
        q = q.distinct(t.Sample.name, t.SampleUdfView.udfname)
        if udfs == 'all':
            q = q.filter(t.SampleUdfView.udfvalue != None)
        else:
            q = q.filter(or_(t.SampleUdfView.udfname.in_(udfs), t.SampleUdfView.udfname == None))
    q = q.filter(t.Artifact.isoriginal)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, project_status=project_status,
                    time_since=time_since)
    return q.all()


def get_samples_and_processes(session, project_name=None, sample_name=None, list_process=None, workstatus=None,
                              time_since=None, project_status='open'):
    """This method runs a query that return the sample name and the processeses they went through"""
    q = session.query(t.Project.name, t.Sample.name, t.ProcessType.displayname,
                      t.Process.workstatus, t.Process.createddate, t.Process.processid) \
        .distinct(t.Sample.name, t.Process.processid) \
        .join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.processiotrackers) \
        .join(t.ProcessIOTracker.process) \
        .join(t.Process.type)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, list_process=list_process,
                    workstatus=workstatus, project_status=project_status, time_since=time_since)
    return q.all()


def get_sample_in_queues_or_progress(session, project_name=None, sample_name=None, list_process=None, time_since=None,
                                     project_status='open'):
    """
    This query gives all of the samples sitting in queue of a allegedly non-qc steps
    See explaination at https://genologics.zendesk.com/hc/en-us/articles/213982003-Reporting-the-contents-of-a-Queue
    """

    # Sub query that find active processes to distinguish between transition that marks Queued artifact
    # and the one that are in progress already
    subq = session.query(t.ProcessIOTracker.inputartifactid, t.Process.processid, t.Process.typeid, t.Process.lastmodifieddate)
    subq = subq.join(t.ProcessIOTracker.process)
    subq = subq.filter(t.Process.workstatus != 'COMPLETE')
    subq = subq.subquery()

    q = session.query(
        t.Project.name, t.Sample.name, t.ProcessType.displayname, t.StageTransition.createddate, t.ProtocolStep.stepid,
        subq.c.processid, subq.c.lastmodifieddate
    )
    q = q.distinct(
        t.Project.name, t.Sample.name, t.ProcessType.displayname, t.StageTransition.createddate, t.ProtocolStep.stepid,
        subq.c.processid, subq.c.lastmodifieddate
    )
    q = q.join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.stage_transitions) \
        .join(t.StageTransition.stage) \
        .join(t.Stage.workflowsection) \
        .join(t.WorkflowSection.labprotocol) \
        .join(t.LabProtocol.protocolsteps) \
        .join(t.ProtocolStep.processtype) \
        .join(t.WorkflowSection.labworkflow)
    q = q.outerjoin(subq, and_(subq.c.inputartifactid == t.Artifact.artifactid,
                               subq.c.typeid == t.ProcessType.typeid))

    q = q.order_by(t.Project.name, t.Sample.name, t.ProcessType.displayname)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, list_process=list_process,
                    project_status=project_status, time_since=time_since)
    # StageTransition.workflowrunid is positive when the transition is not
    # complete and negative when the transition is completed
    q = q.filter(t.StageTransition.workflowrunid > 0)
    # For non-QC processes the protocol step id is the same as the stage stepid.
    # However QC stages have a NULL step ID in the stage table.
    q = q.filter(or_(t.ProtocolStep.stepid == t.Stage.stepid, t.Stage.stepid.is_(None)))
    q = q.filter(t.StageTransition.completedbyid.is_(None))
    return q.all()


def runs_info(session, time_since=None, run_ids=None, run_status=None):
    """
    :param sqlalchemy.orm.Session session:
    :param datetime time_since: date cutoff for a run to be retrieved
    :param list run_ids: filter by specific run ids
    :param list run_status: filter by specific run statuses
    """
    r = None
    s = None
    if run_ids:
        r = session.query(t.Process.processid) \
            .join(t.Process.type) \
            .join(t.Process.udfs) \
            .filter(t.ProcessUdfView.udfname == 'RunID') \
            .filter(t.ProcessUdfView.udfvalue.in_(run_ids)) \
            .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence').subquery('r')

    if run_status:
        s = session.query(t.Process.processid) \
            .join(t.Process.type) \
            .join(t.Process.udfs) \
            .filter(t.ProcessUdfView.udfname == 'Run Status') \
            .filter(t.ProcessUdfView.udfvalue.in_(run_status)) \
            .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence').subquery('s')

    q = session.query(t.Process.createddate, t.Process.processid, t.ProcessUdfView.udfname,
                      t.ProcessUdfView.udfvalue, t.ContainerPlacement.wellyposition, t.Sample.name, t.Project.name) \
        .join(t.Process.type) \
        .join(t.Process.udfs) \
        .join(t.Process.processiotrackers) \
        .join(t.ProcessIOTracker.artifact) \
        .join(t.Artifact.containerplacement) \
        .join(t.ContainerPlacement.container) \
        .join(t.Artifact.samples) \
        .join(t.Sample.project) \
        .filter(t.ProcessUdfView.udfname.in_(('Run Status', 'RunID', 'InstrumentID', 'Cycle', 'Read'))) \
        .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence')

    if time_since:
        q = q.filter(func.date(t.Process.createddate) > func.date(time_since))
    if r is not None:
        q = q.filter(t.Process.processid.in_(r))
    if s is not None:
        q = q.filter(t.Process.processid.in_(s))

    results = q.all()
    return results

def runs_cst(session, time_since=None, run_ids=None, run_status=None):
    """
    :param sqlalchemy.orm.Session session:
    :param datetime time_since: date cutoff for a run to be retrieved
    :param list run_ids: filter by specific run ids
    :param list run_status: filter by specific run statuses
    """
    r = None
    s = None
    if run_ids:
        r = session.query(t.Process.processid) \
            .join(t.Process.type) \
            .join(t.Process.udfs) \
            .filter(t.ProcessUdfView.udfname == 'RunID') \
            .filter(t.ProcessUdfView.udfvalue.in_(run_ids)) \
            .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence').subquery('r')

    if run_status:
        s = session.query(t.Process.processid) \
            .join(t.Process.type) \
            .join(t.Process.udfs) \
            .filter(t.ProcessUdfView.udfname == 'Run Status') \
            .filter(t.ProcessUdfView.udfvalue.in_(run_status)) \
            .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence').subquery('s')

    parent_process_io_tracker = aliased(t.ProcessIOTracker)

    gparent_output_mapping = aliased(t.OutputMapping)
    gparent_process_io_tracker = aliased(t.ProcessIOTracker)
    gparent_process = aliased(t.Process)
    gparent_process_type = aliased(t.ProcessType)

    q = session.query(t.Process.processid, gparent_process.processid, gparent_process.daterun) \
        .distinct(gparent_process.processid) \
        .join(t.Process.type) \
        .join(t.Process.processiotrackers) \
        .join(t.ProcessIOTracker.artifact) \
        .join(t.OutputMapping,            t.OutputMapping.outputartifactid == t.Artifact.artifactid) \
        .join(parent_process_io_tracker,  t.OutputMapping.trackerid == parent_process_io_tracker.trackerid) \
        .join(gparent_output_mapping,     gparent_output_mapping.outputartifactid == parent_process_io_tracker.inputartifactid) \
        .join(gparent_process_io_tracker, gparent_output_mapping.trackerid == gparent_process_io_tracker.trackerid) \
        .join(gparent_process, gparent_process.processid == gparent_process_io_tracker.processid) \
        .join(gparent_process_type,       gparent_process.typeid == gparent_process_type.typeid) \
        .filter(t.ProcessType.displayname == 'AUTOMATED - Sequence')

    if time_since:
        q = q.filter(func.date(t.Process.createddate) > func.date(time_since))
    if r is not None:
        q = q.filter(t.Process.processid.in_(r))
    if s is not None:
        q = q.filter(t.Process.processid.in_(s))

    results = q.all()
    return results
