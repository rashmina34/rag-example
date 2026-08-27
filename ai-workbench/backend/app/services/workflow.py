from app.models.workflow import Workflow


def validate_workflow(
    workflow: Workflow,
):

    if not workflow.steps:
        raise ValueError(
            "Workflow must contain at least one step."
        )

    step_ids = set()

    for step in workflow.steps:

        if step.id in step_ids:
            raise ValueError(
                f"Duplicate step id: {step.id}"
            )

        step_ids.add(step.id)

        if not step.prompt.strip():
            raise ValueError(
                f"Step '{step.name}' has an empty prompt."
            )

    return True