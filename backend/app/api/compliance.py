from fastapi import APIRouter
from app.models.schemas import ComplianceCheckRequest
from app.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge_graph.graph_queries import GraphQueries
from app.rag.vector_store import VectorStore
from app.rag.retriever import HybridRetriever
from app.rag.copilot import RAGCopilot

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

_builder = None
_queries = None
_copilot = None


def _get_copilot():
    global _builder, _queries, _copilot
    if _copilot is None:
        _builder = GraphBuilder()
        _queries = GraphQueries(_builder)
        vector_store = VectorStore()
        retriever = HybridRetriever(vector_store, _queries)
        _copilot = RAGCopilot(retriever)
    return _copilot


@router.post("/check")
async def check_compliance(request: ComplianceCheckRequest):
    copilot = _get_copilot()
    query_parts = []
    if request.equipment_id:
        query_parts.append(f"Check compliance for equipment {request.equipment_id}")
    if request.regulation_id:
        query_parts.append(f"against regulation {request.regulation_id}")
    query = " ".join(query_parts) if query_parts else "Run a general compliance check against all regulations"
    result = copilot.answer(query)
    return {
        "equipment_id": request.equipment_id or "ALL",
        "answer": result["answer"],
        "sources": result["sources"],
    }


@router.get("/report")
async def get_compliance_report():
    builder = GraphBuilder()
    summary = builder.get_graph_summary()
    builder.close()
    return {
        "overall_status": "REVIEW_REQUIRED",
        "total_equipment": summary.get("node_counts", {}).get("Equipment", 0),
        "total_regulations": summary.get("node_counts", {}).get("Regulation", 0),
        "coverage_percentage": 0.0,
        "gaps": [],
    }