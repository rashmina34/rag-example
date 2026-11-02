from uuid import uuid4

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlalchemy.orm import Session

from app.models.database import get_db

from app.models.evaluation_db import (
    EvalResultDB,
    EvalRunDB,
)

from app.services.evaluation import (
    MAX_CASES,
    run_evaluation,
)


router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"],
)


class EvalCase(BaseModel):
    question: str = Field(min_length=1)

    # What a correct answer says. Used by the AI judge in "full" mode.
    reference_answer: str = ""

    # A phrase that must appear in the chunk that holds the answer.
    # Used to check whether retrieval found the right chunk.
    evidence: str = ""


class EvalRunRequest(BaseModel):
    label: str = ""

    mode: str = "retrieval"

    document_id: str | None = None

    top_k: int = Field(default=3, ge=1, le=20)

    chunk_size: int | None = None

    chunk_overlap: int | None = None

    cases: list[EvalCase] = Field(
        min_length=1,
        max_length=MAX_CASES,
    )


def serialize_run(run: EvalRunDB) -> dict:

    return {
        "id": run.id,
        "label": run.label,
        "mode": run.mode,
        "document_id": run.document_id,
        "top_k": run.top_k,
        "chunk_size": run.chunk_size,
        "chunk_overlap": run.chunk_overlap,
        "question_count": run.question_count,
        "hit_rate": run.hit_rate,
        "mrr": run.mrr,
        "correctness": run.correctness,
        "faithfulness": run.faithfulness,
        "created_at": run.created_at,
    }


def serialize_result(result: EvalResultDB) -> dict:

    return {
        "question": result.question,
        "reference_answer": result.reference_answer,
        "evidence": result.evidence,
        "retrieved_rank": result.retrieved_rank,
        "answer": result.answer,
        "correct": result.correct,
        "faithful": result.faithful,
        "judge_reason": result.judge_reason,
        "error": result.error,
    }


@router.post("/run")
def run(
    request: EvalRunRequest,
    db: Session = Depends(get_db),
):
    """Run every test question through the RAG pipeline and score it.

    mode "retrieval": only checks whether the right chunk was found.
    No answer is generated, so it is fast and uses no generation quota.

    mode "full": also generates each answer and has an AI judge grade
    it for correctness and faithfulness.
    """

    cases = [case.model_dump() for case in request.cases]

    try:

        results, summary = run_evaluation(
            cases=cases,
            mode=request.mode,
            top_k=request.top_k,
            document_id=request.document_id,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    run_record = EvalRunDB(
        id=str(uuid4()),
        label=request.label.strip(),
        mode=request.mode,
        document_id=request.document_id,
        top_k=request.top_k,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        question_count=len(results),
        **summary,
    )

    db.add(run_record)

    for position, result in enumerate(results):

        db.add(
            EvalResultDB(
                id=str(uuid4()),
                run_id=run_record.id,
                position=position,
                **result,
            )
        )

    db.commit()

    db.refresh(run_record)

    return {
        **serialize_run(run_record),
        "results": [
            serialize_result(result)
            for result in run_record.results
        ],
    }


@router.get("/runs")
def list_runs(
    db: Session = Depends(get_db),
):

    runs = (
        db.query(EvalRunDB)
        .order_by(EvalRunDB.created_at.desc())
        .all()
    )

    return [serialize_run(run) for run in runs]


@router.get("/runs/{run_id}")
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
):

    run_record = db.get(EvalRunDB, run_id)

    if run_record is None:

        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    return {
        **serialize_run(run_record),
        "results": [
            serialize_result(result)
            for result in run_record.results
        ],
    }


@router.delete("/runs/{run_id}")
def delete_run(
    run_id: str,
    db: Session = Depends(get_db),
):

    run_record = db.get(EvalRunDB, run_id)

    if run_record is None:

        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    db.delete(run_record)

    db.commit()

    return {"status": "deleted", "id": run_id}
