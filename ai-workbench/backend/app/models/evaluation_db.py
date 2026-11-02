from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean
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


class EvalRunDB(Base):

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    label: Mapped[str] = mapped_column(
        String(255),
        default="",
    )

    mode: Mapped[str] = mapped_column(
        String(20),
    )

    document_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    top_k: Mapped[int] = mapped_column(Integer)

    # Informational: how the document was chunked when it was uploaded.
    chunk_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    chunk_overlap: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    question_count: Mapped[int] = mapped_column(Integer)

    hit_rate: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    mrr: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    correctness: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    faithfulness: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    results = relationship(
        "EvalResultDB",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvalResultDB.position",
    )


class EvalResultDB(Base):

    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )

    run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_runs.id"),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(Integer)

    question: Mapped[str] = mapped_column(Text)

    reference_answer: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    evidence: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    # 1-based rank of the first retrieved chunk that contains the
    # evidence, or null when it was not retrieved at all.
    retrieved_rank: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    answer: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    correct: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    faithful: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )

    judge_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    run = relationship(
        "EvalRunDB",
        back_populates="results",
    )
