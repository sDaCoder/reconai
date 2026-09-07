from collections.abc import AsyncIterable

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse, ServerSentEvent
import uvicorn
from pydantic import BaseModel
from sqlmodel import Session, func, select

from agent.recon_agent import run as run_recon_agent, stream as stream_recon_agent
from db_connection import engine
from models import ReconciliationCase

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_origin_regex=r"https://reconai(-[a-z0-9-]+)?\.vercel\.app$",
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/reconciliation-cases")
def list_reconciliation_cases() -> list[ReconciliationCase]:
    with Session(engine) as session:
        return session.exec(select(ReconciliationCase)).all()

class PaginatedReconciliationCases(BaseModel):
    items: list[ReconciliationCase]
    page: int
    page_size: int
    total: int
    total_pages: int

@app.get("/reconciliation-cases/page")
def list_reconciliation_cases_page(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
) -> PaginatedReconciliationCases:
    with Session(engine) as session:
        total = session.exec(select(func.count()).select_from(ReconciliationCase)).one()
        total_pages = max(1, -(-total // page_size))
        page = min(page, total_pages)
        items = session.exec(
            select(ReconciliationCase)
            .order_by(ReconciliationCase.case_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return PaginatedReconciliationCases(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
        )

class ReconcileRequest(BaseModel):
    query: str

class ReconcileResponse(BaseModel):
    result: str

@app.post("/reconcile")
def reconcile(request: ReconcileRequest) -> ReconcileResponse:
    return ReconcileResponse(result=run_recon_agent(request.query))

@app.post("/reconcile/stream", response_class=EventSourceResponse)
async def reconcile_stream(request: ReconcileRequest) -> AsyncIterable[ServerSentEvent]:
    async for token in stream_recon_agent(request.query):
        yield ServerSentEvent(raw_data=token, event="token")

if __name__ == "__main__":
    uvicorn.run("hello:app", host="0.0.0.0", port=8000)