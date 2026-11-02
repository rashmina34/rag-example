import re
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from app.services.llm import generate_json
from app.services.rag import answer_question
from app.services.retrieval import retrieve


MAX_CASES = 20

# Questions are evaluated a few at a time to keep a run short without
# hammering the model API.
MAX_WORKERS = 2


class Verdict(BaseModel):
    correct: bool

    faithful: bool

    reason: str


JUDGE_SYSTEM_PROMPT = """
You are a strict grader for a question answering system.

You get a QUESTION, a REFERENCE ANSWER written by a human, the CONTEXT
the system retrieved, and the system's ANSWER.

Decide two things:

1. correct: does the ANSWER agree with the REFERENCE ANSWER on the
   facts that matter? Extra detail is fine. Missing or contradicting
   the key facts is not. If the answer says the information is not
   available, it is not correct.
2. faithful: is every claim in the ANSWER supported by the CONTEXT?
   An answer that says the information is not available is faithful.
   Claims that only come from outside knowledge are not faithful.

Give a one sentence reason.
""".strip()


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace so matching ignores line breaks."""

    return re.sub(r"\s+", " ", text).strip().lower()


def retrieved_rank(
    chunk_texts: list[str],
    evidence: str,
) -> int | None:
    """1-based rank of the first chunk containing the evidence phrase."""

    needle = normalize(evidence)

    if not needle:
        return None

    for index, text in enumerate(chunk_texts):

        if needle in normalize(text):
            return index + 1

    return None


def judge_answer(
    question: str,
    reference_answer: str,
    context: str,
    answer: str,
) -> Verdict:

    prompt = f"""
QUESTION:
{question}

REFERENCE ANSWER:
{reference_answer}

CONTEXT:
{context}

ANSWER:
{answer}
""".strip()

    return generate_json(
        user_prompt=prompt,
        schema=Verdict,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        temperature=0.0,
    )


def evaluate_case(
    case: dict,
    mode: str,
    top_k: int,
    document_id: str | None,
) -> dict:
    """Run one test question. Never raises: failures are recorded."""

    result = {
        "question": case["question"],
        "reference_answer": case.get("reference_answer", ""),
        "evidence": case.get("evidence", ""),
        "retrieved_rank": None,
        "answer": None,
        "correct": None,
        "faithful": None,
        "judge_reason": None,
        "error": None,
    }

    try:

        if mode == "retrieval":

            chunks = retrieve(
                query=case["question"],
                top_k=top_k,
                document_id=document_id,
            )

            texts = [chunk.text for chunk in chunks]

        else:

            rag = answer_question(
                question=case["question"],
                top_k=top_k,
                document_id=document_id,
            )

            texts = [
                source["text"]
                for source in rag["sources"]
            ]

            result["answer"] = rag["answer"]

        result["retrieved_rank"] = retrieved_rank(
            texts,
            result["evidence"],
        )

        if mode == "full" and result["reference_answer"].strip():

            verdict = judge_answer(
                question=case["question"],
                reference_answer=result["reference_answer"],
                context="\n\n".join(texts),
                answer=result["answer"],
            )

            result["correct"] = verdict.correct
            result["faithful"] = verdict.faithful
            result["judge_reason"] = verdict.reason

    except Exception as error:

        result["error"] = str(error)[:300]

    return result


def average(values: list[float]) -> float | None:

    return sum(values) / len(values) if values else None


def summarize(
    results: list[dict],
    mode: str,
) -> dict:
    """Aggregate per-question results into the run's headline numbers.

    Questions that errored are left out of every average.
    """

    ok = [r for r in results if not r["error"]]

    with_evidence = [
        r for r in ok if r["evidence"].strip()
    ]

    summary = {
        "hit_rate": average(
            [
                1.0 if r["retrieved_rank"] else 0.0
                for r in with_evidence
            ]
        ),
        "mrr": average(
            [
                1.0 / r["retrieved_rank"]
                if r["retrieved_rank"]
                else 0.0
                for r in with_evidence
            ]
        ),
        "correctness": None,
        "faithfulness": None,
    }

    if mode == "full":

        judged = [r for r in ok if r["correct"] is not None]

        summary["correctness"] = average(
            [1.0 if r["correct"] else 0.0 for r in judged]
        )

        summary["faithfulness"] = average(
            [1.0 if r["faithful"] else 0.0 for r in judged]
        )

    return summary


def run_evaluation(
    cases: list[dict],
    mode: str,
    top_k: int,
    document_id: str | None,
) -> tuple[list[dict], dict]:

    if not cases:
        raise ValueError("Add at least one test question.")

    if len(cases) > MAX_CASES:
        raise ValueError(
            f"At most {MAX_CASES} test questions per run."
        )

    if mode not in ("retrieval", "full"):
        raise ValueError(
            "mode must be 'retrieval' or 'full'."
        )

    if top_k <= 0:
        raise ValueError("top_k must be greater than 0.")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:

        results = list(
            pool.map(
                lambda case: evaluate_case(
                    case,
                    mode,
                    top_k,
                    document_id,
                ),
                cases,
            )
        )

    return results, summarize(results, mode)
