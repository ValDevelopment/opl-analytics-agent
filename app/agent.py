from app.db import execute_query
from app.llm import generate_sql, repair_sql, explain_results
from typing import Any

from pydantic import BaseModel

from app.db import execute_query
from app.llm import generate_sql, repair_sql, explain_results


class AgentResponse(BaseModel):
    question: str
    sql: str
    description: str
    results: list[dict[str, Any]]
    answer: str
    was_repaired: bool
    error: str | None = None


def answer_question(question: str) -> AgentResponse:
    generated = generate_sql(question)
    was_repaired = False

    try:
        results = execute_query(generated.sql)

    except Exception as error:
        repaired = repair_sql(
            question,
            generated.sql,
            str(error),
        )

        try:
            results = execute_query(repaired.sql)
            generated = repaired
            was_repaired = True

        except Exception as repair_error:
            return AgentResponse(
                question=question,
                sql=repaired.sql,
                description=repaired.description,
                results=[],
                answer="",
                was_repaired=True,
                error=str(repair_error),
            )

    answer = explain_results(
        question,
        generated.sql,
        results,
    )

    return AgentResponse(
        question=question,
        sql=generated.sql,
        description=generated.description,
        results=results,
        answer=answer,
        was_repaired=was_repaired,
    )