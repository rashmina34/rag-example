from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.models.database import Base


class WorkflowDB(Base):

    __tablename__ = "workflows"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    steps = relationship(
        "WorkflowStepDB",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStepDB.position",
    )


class WorkflowStepDB(Base):

    __tablename__ = "workflow_steps"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    type: Mapped[str] = mapped_column(
        String(50),
        default="prompt",
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.7,
    )

    workflow = relationship(
        "WorkflowDB",
        back_populates="steps",
    )


class WorkflowExecutionDB(Base):

    __tablename__ = "workflow_executions"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    workflow_id: Mapped[str] = mapped_column(
        ForeignKey("workflows.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="running",
    )

    input: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    completed_at: Mapped[
        Optional[datetime]
    ] = mapped_column(
        DateTime,
        nullable=True,
    )


class WorkflowStepExecutionDB(Base):

    __tablename__ = "workflow_step_executions"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    execution_id: Mapped[str] = mapped_column(
        ForeignKey("workflow_executions.id"),
        nullable=False,
    )

    step_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="running",
    )

    input: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    completed_at: Mapped[
        Optional[datetime]
    ] = mapped_column(
        DateTime,
        nullable=True,
    )