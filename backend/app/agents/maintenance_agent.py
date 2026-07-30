from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.knowledge_graph.graph_queries import GraphQueries


class MaintenanceAgent:
    def __init__(self, graph_queries: GraphQueries):
        self.graph_queries = graph_queries
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=0.1,
            num_predict=512,
            num_ctx=2048,
            timeout=120,
        )

    def run(self, query: str) -> dict:
        from app.utils.helpers import EQUIPMENT_TYPE_KEYWORDS

        query_lower = query.lower()
        equipment_ids = []

        if "#" in query or "id:" in query.lower():
            import re
            id_match = re.search(r"(?:#|id:)\s*([A-Z0-9_-]{3,20})", query, re.IGNORECASE)
            if id_match:
                equipment_ids = [id_match.group(1)]

        if not equipment_ids:
            for keyword in EQUIPMENT_TYPE_KEYWORDS:
                if keyword in query_lower:
                    results = self.graph_queries.search(keyword, limit=3)
                    equipment_ids = [r["id"] for r in results]
                    break

        context_parts = []
        sources = []

        for eq_id in equipment_ids[:3]:
            incidents = self.graph_queries.get_incidents_for_equipment(eq_id)
            work_orders = self.graph_queries.get_work_orders_for_equipment(eq_id)

            if incidents:
                context_parts.append(f"\nIncidents for {eq_id}:")
                for inc in incidents[:5]:
                    context_parts.append(f"- {inc.get('date', '')}: {inc.get('description', '')} (Severity: {inc.get('severity', '')})")
                    sources.append(f"Incident {inc.get('incident_id', '')}")

            if work_orders:
                context_parts.append(f"\nWork Orders for {eq_id}:")
                for wo in work_orders[:5]:
                    context_parts.append(f"- [{wo.get('status', '')}] {wo.get('wo_type', '')} - Priority: {wo.get('priority', '')}")
                    sources.append(f"WO {wo.get('work_order_id', '')}")

        if not context_parts:
            context_parts.append("No specific maintenance data found in the knowledge graph.")

        context = "\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a maintenance intelligence agent for industrial equipment.
Analyze the maintenance history, incidents, and work orders to provide insights.

Provide:
1. Summary of the equipment's maintenance state
2. Any recurring failures or patterns
3. Risk assessment
4. Recommended actions

Be specific and data-driven. Reference the actual data points from the context."""),
            ("human", "Query: {query}\n\nMaintenance Data:\n{context}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"query": query, "context": context})

        return {
            "answer": response.content if hasattr(response, "content") else str(response),
            "sources": sources,
        }
