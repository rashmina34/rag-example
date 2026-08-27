from sqlalchemy.orm import Session

from app.models.workflow import Workflow
from app.models.workflow import WorkflowCreate

from app.models.workflow_db import WorkflowDB
from app.models.workflow_db import WorkflowStepDB


def create_workflow(
    db: Session,
    workflow: WorkflowCreate,
):

    db_workflow = WorkflowDB(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
    )

    db.add(db_workflow)

    for position, step in enumerate(
        workflow.steps
    ):

        db_step = WorkflowStepDB(
            id=step.id,
            workflow_id=workflow.id,
            position=position,
            name=step.name,
            type=step.type,
            system_prompt=step.system_prompt,
            prompt=step.prompt,
            temperature=step.temperature,
        )

        db.add(db_step)

    db.commit()

    db.refresh(db_workflow)

    return db_workflow


def get_workflow(
    db: Session,
    workflow_id: str,
):

    return (
        db.query(WorkflowDB)
        .filter(
            WorkflowDB.id == workflow_id
        )
        .first()
    )


def list_workflows(
    db: Session,
):

    return (
        db.query(WorkflowDB)
        .order_by(
            WorkflowDB.created_at.desc()
        )
        .all()
    )


def delete_workflow(
    db: Session,
    workflow_id: str,
):

    workflow = get_workflow(
        db,
        workflow_id,
    )

    if workflow is None:
        return False

    db.delete(workflow)

    db.commit()

    return True


def db_to_workflow(
    db_workflow: WorkflowDB,
) -> Workflow:

    steps = []

    for step in db_workflow.steps:

        steps.append(
            {
                "id": step.id,
                "name": step.name,
                "type": step.type,
                "system_prompt": step.system_prompt,
                "prompt": step.prompt,
                "temperature": step.temperature,
            }
        )

    return Workflow(
        id=db_workflow.id,
        name=db_workflow.name,
        description=db_workflow.description,
        steps=steps,
    )