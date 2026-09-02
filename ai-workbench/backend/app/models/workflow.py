from typing import Literal

from pydantic import BaseModel
from pydantic import Field


StepType = Literal[
    "prompt",
    "transform",
]


class WorkflowStep(BaseModel):
    id: str

    name: str

    type: StepType = "prompt"

    system_prompt: str = (
        "You are a helpful AI assistant."
    )

    prompt: str

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
    )


class Workflow(BaseModel):
    id: str

    name: str

    description: str = ""

    steps: list[WorkflowStep] = Field(
        default_factory=list
    )


class WorkflowCreate(BaseModel):
    id: str

    name: str

    description: str = ""

    steps: list[WorkflowStep] = Field(
        default_factory=list
    )


class WorkflowUpdate(BaseModel):
    name: str

    description: str = ""

    steps: list[WorkflowStep] = Field(
        default_factory=list
    )


class WorkflowExecuteRequest(BaseModel):
    input: str
    

#alternative of above others schema
class WorkflowStepSchema(BaseModel):
    id: str
    type: str
    input: str

class WorkflowSchema(BaseModel):
    name: str
    description: str = ""
    steps: list[WorkflowStepSchema] = Field(
        default_factory=list
    )