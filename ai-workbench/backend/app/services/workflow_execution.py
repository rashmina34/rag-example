from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session
from app.services.rag import answer_question

from app.models.workflow import Workflow

from app.models.workflow_db import (
    WorkflowExecutionDB,
    WorkflowStepExecutionDB,
)

from app.services.llm import generate_response
from app.services.prompts import render_prompt


def execute_and_record_workflow(
    db: Session,
    workflow: Workflow,
    initial_input: str,
):

    execution_id = str(uuid4())

    execution = WorkflowExecutionDB(
        id=execution_id,
        workflow_id=workflow.id,
        status="running",
        input=initial_input,
        started_at=datetime.utcnow(),
    )

    db.add(execution)

    db.commit()

    context = {
        "input": initial_input
    }

    results = []

    try:

        for position, step in enumerate(
            workflow.steps
        ):

            step_execution_id = str(uuid4())

            started_at = datetime.utcnow()

            rendered_prompt = render_prompt(
                step.prompt,
                context,
            )

            step_execution = (
                WorkflowStepExecutionDB(
                    id=step_execution_id,
                    execution_id=execution_id,
                    step_id=step.id,
                    position=position,
                    status="running",
                    input=rendered_prompt,
                    started_at=started_at,
                )
            )

            db.add(step_execution)

            db.commit()

            try:
                if step.type == "llm":
                    
                    output = generate_response(
                        system_prompt=step.system_prompt,
                        user_prompt=rendered_prompt,
                        temperature=step.temperature,
                    )
                elif step.type == "rag":
                    rag_result = answer_question(
                    question=rendered_prompt,
                    top_k=5,
                    )

                    output = rag_result["answer"]
                else:
                     raise ValueError(
                        f"Unsupported workflow step type: {step.type}"
                     )


                step_execution.status = (
                    "completed"
                )

                step_execution.output = output

                step_execution.completed_at = (
                    datetime.utcnow()
                )

                db.commit()

                context[
                    f"{step.id}.output"
                ] = output

                results.append(
                    {
                        "step_id": step.id,
                        "step_name": step.name,
                        "output": output,
                    }
                )

            except Exception as error:

                step_execution.status = "failed"

                step_execution.error = str(
                    error
                )

                step_execution.completed_at = (
                    datetime.utcnow()
                )

                db.commit()

                raise

        if results:

            final_output = results[-1][
                "output"
            ]

        else:

            final_output = ""

        execution.status = "completed"

        execution.output = final_output

        execution.completed_at = (
            datetime.utcnow()
        )

        db.commit()

        return {
            "execution_id": execution_id,
            "workflow_id": workflow.id,
            "status": "completed",
            "output": final_output,
            "steps": results,
        }

    except Exception as error:

        execution.status = "failed"

        execution.error = str(error)

        execution.completed_at = (
            datetime.utcnow()
        )

        db.commit()

        raise