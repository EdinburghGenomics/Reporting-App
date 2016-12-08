from sqlalchemy import or_
import genologics_sql.tables as t


def add_filters(q, **kwargs):
    if kwargs.get('project_name'):
        q = q.filter(t.Project.name == kwargs.get('project_name'))
    if kwargs.get('sample_name'):
        q = q.filter(t.Sample.name == kwargs.get('sample_name'))
    if kwargs.get('list_process'):
        q = q.filter(t.ProcessType.displayname.in_(kwargs.get('list_process')))
    if kwargs.get('only_open_project'):
        q = q.filter(t.Project.closedate == None)
    if kwargs.get('workstatus'):
        q = q.filter(t.Process.workstatus == kwargs.get('workstatus'))
    return q


def get_project_info(session, project_name=None, only_open_project=True, udfs=None):
    """This method runs a query that return the get projects and specific udfs"""
    q = session.query(t.Project.name, t.Project.opendate, t.Researcher.firstname, t.Researcher.lastname,
                      t.EntityUdfView.udfname, t.EntityUdfView.udfvalue) \
        .distinct(t.Project.name) \
        .outerjoin(t.Project.researcher) \
        .outerjoin(t.Project.udfs)
    q = add_filters(q, project_name=project_name, only_open_project=only_open_project)
    if udfs:
        q = q.distinct(t.Project.name, t.EntityUdfView.udfname)
        q = q.filter(or_(t.EntityUdfView.udfname.in_(udfs), t.EntityUdfView.udfname == None))
    return q.all()


def get_project(session, project_name=None, only_open_project=True, udfs=None):
    """This method runs a query that return the get projects and specific udfs"""
    q = session.query(t.Project.name, t.Project.opendate, t.Researcher.firstname, t.Researcher.lastname,
                      t.EntityUdfView.udfname, t.EntityUdfView.udfvalue) \
        .distinct(t.Project.name) \
        .outerjoin(t.Project.researcher) \
        .outerjoin(t.Project.udfs)
    q = add_filters(q, project_name=project_name, only_open_project=only_open_project)
    if udfs:
        q = q.filter(or_(t.EntityUdfView.udfname.in_(udfs), t.EntityUdfView.udfname == None))
    return q.all()

def get_sample_container_placement(session, project_name=None, sample_name=None, only_open_project=True):
    """This method runs a query that return samples and its associated original container"""
    q = session.query(t.Project.name, t.Sample.name, t.Container.name,
                      t.ContainerPlacement.wellxposition, t.ContainerPlacement.wellyposition) \
        .distinct(t.Sample.name) \
        .join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.containerplacement) \
        .join(t.ContainerPlacement.container)
    q = q.filter(t.Artifact.isoriginal)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, only_open_project=only_open_project)
    return q.all()

def get_samples_and_processes(session, project_name=None, sample_name=None, list_process=None, workstatus=None, only_open_project=True):
    """This method runs a query that return the sample name and the processeses they went through"""
    q = session.query(t.Project.name, t.Sample.name, t.ProcessType.displayname,
                      t.Process.workstatus, t.Process.createddate) \
        .distinct(t.Sample.name, t.Process.processid) \
        .join(t.Sample.project) \
        .join(t.Sample.artifacts) \
        .join(t.Artifact.processiotrackers) \
        .join(t.ProcessIOTracker.process) \
        .join(t.Process.type)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, list_process=list_process,
                    workstatus=workstatus, only_open_project=only_open_project)
    return q.all()


def non_QC_queues(session, project_name=None, sample_name=None, list_process=None, only_open_project=True):
    """
    This query gives all of the samples sitting in queue of a aledgedly non-qc steps
    """
    q = session.query(
        t.Project.name, t.Sample.name, t.ProcessType.displayname, t.StageTransition.createddate
    )
    q = q.distinct(
        t.Project.name, t.Sample.name, t.ProcessType.displayname, t.StageTransition.createddate
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
    q = q.order_by(t.Project.name, t.Sample.name, t.ProcessType.displayname)
    q = add_filters(q, project_name=project_name, sample_name=sample_name, list_process=list_process,
                    only_open_project=only_open_project)
    # StageTransition.workflowrunid is positive when the transition is not
    # complete and negative when the transition is completed
    q = q.filter(t.StageTransition.workflowrunid > 0)
    q = q.filter(t.StageTransition.completedbyid.is_(None))
    return q.all()


if __name__ == "__main__":
    from rest_api.limsdb import get_session
    session = get_session()
    res = get_sample_container_placement(session, sample_name='X16137P001E01')
    print('\n'.join([str(r) for r in res]))
