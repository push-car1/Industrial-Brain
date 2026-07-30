from fastapi import APIRouter, Query, HTTPException
from app.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge_graph.graph_queries import GraphQueries

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])

_builder = None
_queries = None


def _get_graph():
    global _builder, _queries
    if _builder is None:
        _builder = GraphBuilder()
        _queries = GraphQueries(_builder)
    return _builder, _queries


@router.get("/summary")
async def get_summary():
    try:
        builder, _ = _get_graph()
        return builder.get_graph_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_nodes(q: str = Query("", min_length=1)):
    try:
        _, queries = _get_graph()
        results = queries.search(q)
        return {"results": results}
    except Exception as e:
        return {"results": [], "error": str(e)}


@router.get("/explore")
async def explore_graph(node_id: str = Query(...), depth: int = 2):
    try:
        builder, _ = _get_graph()
        subgraph = builder.get_subgraph(node_id, depth)
        if not subgraph["nodes"]:
            return {"nodes": [], "relationships": [], "message": f"Node '{node_id}' not found"}
        return subgraph
    except Exception as e:
        return {"nodes": [], "relationships": [], "error": str(e)}


@router.get("/equipment/{equipment_id}")
async def get_equipment_detail(equipment_id: str):
    try:
        _, queries = _get_graph()
        return {
            "documents": queries.get_equipment_with_documents(equipment_id),
            "incidents": queries.get_incidents_for_equipment(equipment_id),
            "work_orders": queries.get_work_orders_for_equipment(equipment_id),
            "active_permits": queries.get_active_permits_for_equipment(equipment_id),
        }
    except Exception as e:
        return {"error": str(e), "equipment_id": equipment_id}


@router.get("/equipment/{equipment_id}/incidents")
async def get_equipment_incidents(equipment_id: str):
    try:
        _, queries = _get_graph()
        return {"incidents": queries.get_incidents_for_equipment(equipment_id)}
    except Exception as e:
        return {"incidents": [], "error": str(e)}


@router.get("/equipment/{equipment_id}/work-orders")
async def get_equipment_work_orders(equipment_id: str):
    try:
        _, queries = _get_graph()
        return {"work_orders": queries.get_work_orders_for_equipment(equipment_id)}
    except Exception as e:
        return {"work_orders": [], "error": str(e)}


@router.get("/conflicts/permits")
async def get_permit_conflicts():
    try:
        _, queries = _get_graph()
        return {"conflicts": queries.find_simultaneous_permit_conflicts()}
    except Exception as e:
        return {"conflicts": [], "error": str(e)}
