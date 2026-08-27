from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.models.database import get_db

from app.models.workflow import WorkflowCreate
from app.models.workflow import WorkflowExecuteRequest

from app.models.workflow_db import (
    WorkflowExecutionDB,
    WorkflowStepExecutionDB,
)

from app.services.workflow_execution import (
    execute_and_record_workflow,
)

from app.services.workflow_repository import (
    create_workflow,
    db_to_workflow,
    delete_workflow,
    get_workflow,
    list_workflows,
)


router = APIRouter(
    prefix="/workflows",
    tags=["workflows"],
)


@router.post("")
def create(
    workflow: WorkflowCreate,
    db: Session = Depends(get_db),
):

    existing = get_workflow(
        db,
        workflow.id,
    )

    if existing:

        raise HTTPException(
            status_code=409,
            detail="Workflow already exists.",
        )

    created = create_workflow(
        db,
        workflow,
    )

    return {
        "id": created.id,
        "name": created.name,
        "description": created.description,
    }


@router.get("")
def get_all(
    db: Session = Depends(get_db),
):

    workflows = list_workflows(db)

    return [
        {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
        for workflow in workflows
    ]


@router.get("/{workflow_id}")
def get_one(
    workflow_id: str,
    db: Session = Depends(get_db),
):

    workflow = get_workflow(
        db,
        workflow_id,
    )

    if workflow is None:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found.",
        )

    return {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "steps": [
            {
                "id": step.id,
                "name": step.name,
                "type": step.type,
                "system_prompt": step.system_prompt,
                "prompt": step.prompt,
                "temperature": step.temperature,
            }
            for step in workflow.steps
        ],
    }


@router.delete("/{workflow_id}")
def delete(
    workflow_id: str,
    db: Session = Depends(get_db),
):

    deleted = delete_workflow(
        db,
        workflow_id,
    )

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found.",
        )

    return {
        "status": "deleted",
        "id": workflow_id,
    }


@router.post("/{workflow_id}/execute")
def execute_workflow_endpoint(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    db: Session = Depends(get_db),
):
    workflow_db = get_workflow(
        db,
        workflow_id,
    )

    if workflow_db is None:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found.",
        )

    workflow = db_to_workflow(
        workflow_db
    )

    try:

        return execute_and_record_workflow(
            db=db,
            workflow=workflow,
            initial_input=request.input,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        )


@router.get("/{workflow_id}/executions")
def get_execution_history(
    workflow_id: str,
    db: Session = Depends(get_db),
):

    workflow = get_workflow(
        db,
        workflow_id,
    )

    if workflow is None:

        raise HTTPException(
            status_code=404,
            detail="Workflow not found.",
        )

    executions = (
        db.query(WorkflowExecutionDB)
        .filter(
            WorkflowExecutionDB.workflow_id
            == workflow_id
        )
        .order_by(
            WorkflowExecutionDB.started_at.desc()
        )
        .all()
    )

    return [
        {
            "id": execution.id,
            "status": execution.status,
            "input": execution.input,
            "output": execution.output,
            "error": execution.error,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
        }
        for execution in executions
    ]


@router.get(
    "/{workflow_id}/executions/{execution_id}"
)
def get_execution(
    workflow_id: str,
    execution_id: str,
    db: Session = Depends(get_db),
):

    execution = (
        db.query(WorkflowExecutionDB)
        .filter(
            WorkflowExecutionDB.id
            == execution_id,
            WorkflowExecutionDB.workflow_id
            == workflow_id,
        )
        .first()
    )

    if execution is None:

        raise HTTPException(
            status_code=404,
            detail="Execution not found.",
        )

    steps = (
        db.query(
            WorkflowStepExecutionDB
        )
        .filter(
            WorkflowStepExecutionDB.execution_id
            == execution_id
        )
        .order_by(
            WorkflowStepExecutionDB.position
        )
        .all()
    )

    return {
        "id": execution.id,
        "workflow_id": execution.workflow_id,
        "status": execution.status,
        "input": execution.input,
        "output": execution.output,
        "error": execution.error,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "steps": [
            {
                "id": step.id,
                "step_id": step.step_id,
                "position": step.position,
                "status": step.status,
                "input": step.input,
                "output": step.output,
                "error": step.error,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
            }
            for step in steps
        ],
    }