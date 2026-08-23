from fastapi import FastAPI
from pydantic import BaseModel

from app.agent import AgentResponse, answer_question


app = FastAPI(
    title="Natural Language SQL Analytics",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AgentResponse)
def ask(request: QuestionRequest):
    return answer_question(request.question)