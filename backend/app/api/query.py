import uuid
from fastapi import APIRouter
from app.models.schemas import ChatRequest, ChatResponse
from app.rag.vector_store import VectorStore
from app.rag.retriever import HybridRetriever
from app.rag.copilot import RAGCopilot
from app.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge_graph.graph_queries import GraphQueries
from app.agents.rag_agent import RAGAgent
from app.agents.maintenance_agent import MaintenanceAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.lessons_agent import LessonsLearnedAgent

router = APIRouter(prefix="/api/query", tags=["query"])

_conversations = {}
_copilot = None
_orchestrator = None


def _get_copilot():
    global _copilot
    if _copilot is None:
        builder = GraphBuilder()
        queries = GraphQueries(builder)
        vector_store = VectorStore()
        retriever = HybridRetriever(vector_store, queries)
        _copilot = RAGCopilot(retriever)
    return _copilot


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    conv_id = request.conversation_id or str(uuid.uuid4())

    copilot = _get_copilot()
    result = copilot.answer(request.message)

    if conv_id not in _conversations:
        _conversations[conv_id] = []
    _conversations[conv_id].append({
        "role": "user",
        "content": request.message,
    })
    _conversations[conv_id].append({
        "role": "assistant",
        "content": result["answer"],
    })

    return ChatResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        conversation_id=conv_id,
    )


@router.get("/conversations")
async def list_conversations():
    return {
        "conversations": [
            {"id": k, "messages": v[-2:]}
            for k, v in _conversations.items()
        ]
    }


@router.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    messages = _conversations.get(conv_id, [])
    return {"conversation_id": conv_id, "messages": messages}
