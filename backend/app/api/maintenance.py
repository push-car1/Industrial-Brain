from fastapi import APIRouter
from app.models.schemas import MaintenancePredictionRequest, RCARequest
from app.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge_graph.graph_queries import GraphQueries
from app.agents.maintenance_agent import MaintenanceAgent
from app.agents.lessons_agent import LessonsLearnedAgent
from app.rag.vector_store import VectorStore
from app.rag.retriever import HybridRetriever
from app.rag.copilot import RAGCopilot

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])

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


@router.post("/predict")
async def predict_maintenance(request: MaintenancePredictionRequest):
    copilot = _get_copilot()
    query = f"Analyze maintenance needs for equipment {request.equipment_id} for the next {request.days_ahead} days. Include relevant work orders and incidents."
    result = copilot.answer(query)
    return {
        "equipment_id": request.equipment_id,
        "recommendations": [{
            "equipment_id": request.equipment_id,
            "risk_level": "MEDIUM",
            "predicted_failure": "Review maintenance history",
            "recommended_action": result["answer"][:500],
            "probability": 0.5,
        }],
        "details": result["answer"],
    }


@router.post("/rca")
async def root_cause_analysis(request: RCARequest):
    copilot = _get_copilot()
    query = f"Perform root cause analysis: {request.description}"
    if request.equipment_id:
        query = f"Perform root cause analysis for equipment {request.equipment_id}: {request.description}"
    maint_result = copilot.answer(query)
    return {
        "root_causes": ["See analysis below"],
        "contributing_factors": ["Review maintenance logs"],
        "recommendations": [maint_result["answer"][:500]],
        "similar_incidents": [],
        "maintenance_analysis": maint_result["answer"],
        "lessons_analysis": "",
    }